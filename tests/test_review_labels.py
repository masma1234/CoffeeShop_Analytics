"""Explicit annotation mapping, reviewed negatives and source-image integrity."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

from coffee_ops.review_labels import evaluate_review_frames
from coffee_ops.schema import file_hash


@unittest.skipUnless(importlib.util.find_spec("ijson"),"Optional video-evaluation ijson dependency required")
class ReviewLabelTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        image=self.root/"frame-00000002.jpg";image.write_bytes(b"file-hash-fixture-not-an-actual-decoded-image")
        self.manifest={"source_sha256":"clip","width":100,"height":100,"source_classes":{"0":"person","41":"cup"},
            "thresholds":{"0":.5,"41":.5},"frames":[{"frame":2,"seconds":.2,"image":image.name,"image_sha256":file_hash(str(image))}]}
        (self.root/"annotation_frames.json").write_text(json.dumps(self.manifest))
        self.classes=self.root/"classes.txt";self.classes.write_text("cup\n")
        self.labels=self.root/"labels";self.labels.mkdir();self.label=self.labels/"frame-00000002.txt"
        self.label.write_text("0 .5 .5 .2 .2\n")
        raw={"complete":True,"source_identity":"clip","frames":[{"frame":2,"seconds":.2,"detections":[{"class_id":41,"confidence":.9,"bbox":[40,40,60,60]},
            {"class_id":0,"confidence":.99,"bbox":[0,0,50,50]}]}]}
        (self.root/"detections.json").write_text(json.dumps(raw))

    def run_evaluation(self,reviewed=True):
        return evaluate_review_frames(self.root,self.labels,self.classes,reviewed)

    def test_explicit_name_mapping_and_scope_score_only_annotated_classes(self):
        result=self.run_evaluation()
        self.assertEqual(result["annotation_to_model_ids"],{0:41})
        self.assertEqual(result["operating_point_detection"]["precision"],1)
        self.assertEqual(result["raw_proposal_AP"]["mAP50"],1)
        self.assertEqual(result["errors"],[])

    def test_unreviewed_missing_and_unknown_labels_cannot_be_assumed_negative(self):
        with self.assertRaises(ValueError):self.run_evaluation(reviewed=False)
        self.label.unlink()
        with self.assertRaises(ValueError):self.run_evaluation()
        self.label.write_text("1 .5 .5 .2 .2")
        with self.assertRaises(ValueError):self.run_evaluation()

    def test_reviewed_empty_label_is_a_negative_with_a_false_positive(self):
        self.label.write_text("")
        result=self.run_evaluation()
        self.assertEqual(result["operating_point_detection"]["precision"],0)
        self.assertEqual(result["errors"][0]["cause"],"detector_false_positive")

    def test_tampered_source_frame_or_unrecognized_class_name_is_rejected(self):
        self.classes.write_text("coffee_cup")
        with self.assertRaises(ValueError):self.run_evaluation()
        self.classes.write_text("cup")
        (self.root/"frame-00000002.jpg").write_bytes(b"changed")
        with self.assertRaisesRegex(ValueError,"changed"):self.run_evaluation()

    def test_incomplete_or_foreign_journal_is_rejected(self):
        path=self.root/"detections.json";original=json.loads(path.read_text())
        for field,value in [("complete",False),("complete",None),("source_identity","other")]:
            with self.subTest(field=field,value=value):
                path.write_text(json.dumps({**original,field:value}))
                with self.assertRaises(ValueError):self.run_evaluation()

    def test_different_timestamp_and_fractional_frame_are_rejected(self):
        path=self.root/"detections.json";original=path.read_text()
        for field,value in [("seconds",.3),("frame",2.5)]:
            with self.subTest(field=field):
                data=json.loads(original);data["frames"][0][field]=value
                path.write_text(json.dumps(data))
                with self.assertRaises(ValueError):self.run_evaluation()

    def test_duplicate_manifest_frame_or_ambiguous_catalog_is_rejected(self):
        path=self.root/"annotation_frames.json"
        self.manifest["frames"]*=2;path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError,"unique"):self.run_evaluation()
        self.manifest["frames"]=self.manifest["frames"][:1]
        self.manifest["source_classes"]["0"]="cup";path.write_text(json.dumps(self.manifest))
        with self.assertRaisesRegex(ValueError,"Ambiguous"):self.run_evaluation()

    def test_external_image_path_rejected_even_when_hash_matches(self):
        with tempfile.TemporaryDirectory() as outside:
            image=Path(outside)/"frame-00000002.jpg";image.write_bytes(b"external")
            self.manifest["frames"][0].update(image=str(image),image_sha256=file_hash(str(image)))
            (self.root/"annotation_frames.json").write_text(json.dumps(self.manifest))
            with self.assertRaisesRegex(ValueError,"inside review directory"):self.run_evaluation()

    def test_duplicate_or_missing_selected_prediction_is_rejected(self):
        path=self.root/"detections.json";original=json.loads(path.read_text())
        for frames in [original["frames"]*2,[]]:
            with self.subTest(count=len(frames)):
                path.write_text(json.dumps({**original,"frames":frames}))
                with self.assertRaises(ValueError):self.run_evaluation()

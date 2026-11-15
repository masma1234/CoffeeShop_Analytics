"""Optional native PyAV tests: source PTS, annotation exports, replay and failures."""
import copy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from coffee_ops.config import Config
from coffee_ops.event_evaluation import evaluate_events
from coffee_ops.schema import file_hash
from coffee_ops.video_io import source_position,PTSVideoWriter

ROOT=Path(__file__).resolve().parents[1]
HAS_AV=importlib.util.find_spec("av") is not None
PTS=[0,100,250,500,650,1000]


def make_source(path,width=128,height=96):
    import av
    with av.open(str(path),"w") as container:
        stream=container.add_stream("mpeg4",rate=10);stream.width=width;stream.height=height
        stream.pix_fmt="yuv420p";stream.time_base=Fraction(1,1000);stream.codec_context.time_base=Fraction(1,1000)
        stream.codec_context.max_b_frames=0
        for i,pts in enumerate(PTS):
            frame=av.VideoFrame.from_ndarray(np.full((height,width,3),i*15,dtype=np.uint8),format="bgr24")
            frame.pts=pts;frame.time_base=Fraction(1,1000)
            for packet in stream.encode(frame):container.mux(packet)
        for packet in stream.encode():container.mux(packet)


class SourceTimestampTests(unittest.TestCase):
    def test_unavailable_gpu_monitor_reports_unavailable_and_still_stops(self):
        from coffee_ops.resources import ResourceMonitor
        monitor=ResourceMonitor();monitor.smi="nonexistent-coffee-ops-gpu-command"
        monitor.start();result=monitor.stop()
        self.assertEqual(result["gpu_device_samples"],0)
        self.assertIsNone(result["gpu_device_peak_utilization_percent"])
        self.assertFalse(monitor.thread.is_alive())

    def test_missing_nonmonotonic_and_invalid_time_bases_fail(self):
        frame=SimpleNamespace(pts=10,time_base=Fraction(1,1000))
        self.assertEqual(source_position(frame),Fraction(1,100))
        for bad in [SimpleNamespace(pts=None,time_base=Fraction(1,1000)),SimpleNamespace(pts=1,time_base=None),
                    SimpleNamespace(pts=1,time_base=Fraction(-1))]:
            with self.assertRaises(ValueError):source_position(bad)
        with self.assertRaises(ValueError):source_position(frame,Fraction(1,100))

    def test_unreviewed_templates_are_not_ground_truth(self):
        with self.assertRaisesRegex(ValueError,"Unreviewed"):
            evaluate_events({"annotation_status":"unreviewed","events":[]},{"events":[]})


@unittest.skipUnless(HAS_AV,"Optional PyAV video environment required")
class NativeVideoReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
        self.source=self.root/"source.mp4";make_source(self.source)
        original=Config.load(ROOT/"config/example.json");data=copy.deepcopy(original.data)
        data["cameras"][0].update(width=128,height=96,zones=[],motion_threshold=1)
        data["rules"]["authorized_product_zones"]={}
        data["rules"]["product_evidence"]={"interaction_distance_pixels":30,"movement_pixels":3,"minimum_interaction_seconds":.2,"max_gap_seconds":.5}
        data["storage"]["path"]=str(self.root/"operations.db")
        self.config=Config(data,self.root);self.config.validate()
        self.fixture=self.root/"detections.json"
        self.fixture.write_text(json.dumps({"purpose":"pipeline_fixture_not_model_accuracy","frames":[
            {"frame":i,"detections":[{"class_id":0,"bbox":[10,10,30,50],"confidence":.95},
             {"class_id":1,"bbox":[60,60,75,80],"confidence":.9}]} for i in range(len(PTS))]}))

    def review(self,name,**kwargs):
        from coffee_ops.video_review import review_video
        return review_video(self.config,self.source,self.root/name,"shop","video-review","2026-01-01T09:00:00Z",fixture=self.fixture,**kwargs)

    def test_startup_failure_is_preserved_in_failed_processing_summary(self):
        from coffee_ops.detector_startup import DetectorStartupTimeout
        from coffee_ops.video_review import review_video
        metrics={"status":"failed","deadline_seconds":1,"total_seconds":1,
                 "phases":[{"phase":"transformers_import","elapsed_seconds":.1}]}
        failure=DetectorStartupTimeout("Detector startup exceeded 1s deadline; last stage: transformers_import",metrics)
        with patch("coffee_ops.video_review.YOLODetector",side_effect=failure):
            with self.assertRaises(DetectorStartupTimeout):
                review_video(self.config,self.source,self.root/"load-failure","shop","video-review","2026-01-01T09:00:00Z")
        summary=json.loads((self.root/"load-failure/processing_summary.json").read_text())
        self.assertEqual(summary["status"],"failed")
        self.assertEqual(summary["detector_startup"],metrics)
        self.assertEqual(summary["inferred_frames"],0)
        self.assertIsNone(summary["confirmed_handovers"])

    def test_vfr_sampling_preserves_all_frame_pts_and_source_bytes(self):
        import av
        before=file_hash(str(self.source));result=self.review("output",sample_every=2,export_frames_every=.2)
        self.assertEqual(result["status"],"completed")
        self.assertEqual(result["decoded_frames"],6);self.assertEqual(result["inferred_frames"],3)
        self.assertEqual(file_hash(str(self.source)),before)
        with av.open(str(self.root/"output/annotated.mp4")) as movie:
            output_pts=[float(f.pts*f.time_base) for f in movie.decode(video=0)]
        self.assertEqual(len(output_pts),6)
        for actual,expected in zip(output_pts,PTS):self.assertAlmostEqual(actual,expected/1000,places=5)
        rows=[json.loads(x) for x in (self.root/"output/frames.jsonl").read_text().splitlines()]
        self.assertEqual([r["sampled"] for r in rows],[True,False,True,False,True,False])
        self.assertIsNone(result["prepared_drinks"]);self.assertIsNone(result["confirmed_handovers"])
        self.assertEqual(len(json.loads((self.root/"output/detections.json").read_text())["frames"]),3)

    def test_repeated_replay_deduplicates_event_ids_and_existing_outputs_are_protected(self):
        from coffee_ops.video_review import review_video
        self.review("first");self.review("second")
        a=json.loads((self.root/"first/events.json").read_text())["events"]
        b=json.loads((self.root/"second/events.json").read_text())["events"]
        self.assertEqual(a,b)
        with self.assertRaises(FileExistsError):
            review_video(self.config,self.source,self.root/"first","shop","video-review","2026-01-01T09:00:00Z",fixture=self.fixture)

    def test_partial_run_is_explicit_and_unreviewed_label_template_is_rejected(self):
        result=self.review("partial",max_frames=3)
        self.assertEqual(result["decoded_frames"],3)
        template=json.loads((self.root/"partial/event_labels_template.json").read_text())
        with self.assertRaisesRegex(ValueError,"Unreviewed"):evaluate_events(template,{"events":[]})

    def test_corrupt_input_and_wrong_dimensions_do_not_create_output(self):
        from coffee_ops.video_review import review_video,probe_video
        bad=self.root/"bad.mp4";bad.write_bytes(b"not a video")
        with self.assertRaises(OSError):probe_video(bad)
        self.config.camera("shop")["width"]=120
        with self.assertRaisesRegex(ValueError,"dimensions"):
            review_video(self.config,self.source,self.root/"invalid","shop","r","2026-01-01T09:00:00Z",fixture=self.fixture)
        self.assertFalse((self.root/"invalid").exists())

    def test_unreviewed_event_labels_are_rejected_before_expensive_processing(self):
        from coffee_ops.video_review import review_video
        labels=self.root/"labels.json";labels.write_text(json.dumps({"annotation_status":"unreviewed","events":[]}))
        with self.assertRaisesRegex(ValueError,"Unreviewed"):
            review_video(self.config,self.source,self.root/"unreviewed","shop","r","2026-01-01T09:00:00Z",
                         fixture=self.fixture,event_labels=labels)
        self.assertFalse((self.root/"unreviewed").exists())

    def test_failed_encoding_terminates_worker_with_a_deadline(self):
        writer=PTSVideoWriter(self.root/"terminated.mp4",128,96,"10",timeout=.5)
        writer.process.terminate();writer.process.join(timeout=2)
        try:
            with self.assertRaises((TimeoutError,RuntimeError)):writer.write(np.zeros((96,128,3),dtype=np.uint8),Fraction(0))
        finally:writer.close(abort=True)
        self.assertFalse(writer.process.is_alive())

    def test_odd_output_dimensions_are_padded_and_pts_rounding_is_bounded(self):
        import av
        writer=PTSVideoWriter(self.root/"odd.mp4",127,95,"10")
        try:
            writer.write(np.zeros((95,127,3),dtype=np.uint8),Fraction(0))
            writer.write(np.zeros((95,127,3),dtype=np.uint8),Fraction(123456,1000000))
            writer.close()
        finally:writer.close(abort=True)
        self.assertLessEqual(writer.max_rounding_error,1/120000)
        with av.open(str(self.root/"odd.mp4")) as container:
            frames=list(container.decode(video=0))
        self.assertEqual((frames[0].width,frames[0].height),(128,96))
        self.assertAlmostEqual(float(frames[1].pts*frames[1].time_base),.123456,delta=1/60000)

    def test_labeled_event_scoring_reports_missed_completion_without_inventing_a_cause(self):
        labels=self.root/"reviewed-events.json"
        document={"schema_version":1,"annotation_status":"reviewed","clip_id":"video-review","camera_id":"shop",
            "recording_group":"synthetic-fixture","annotation_version":"1","time_origin_utc":"2026-01-01T09:00:00Z",
            "source_identity":file_hash(str(self.source)),"duration_seconds":1.1,"scored_event_kinds":["preparation_completed"],
            "provenance":{"kind":"synthetic_logic_fixture"},"events":[{"kind":"preparation_completed","seconds":.5,"status":"observed"}]}
        labels.write_text(json.dumps(document))
        result=self.review("labeled",event_labels=labels)
        score=json.loads((self.root/"labeled/event_evaluation.json").read_text())
        report=json.loads((self.root/"labeled/error_report.json").read_text())
        self.assertEqual(score["fn"],1);self.assertEqual(score["event_recall"],0)
        self.assertIsNone(result["prepared_drinks"])
        self.assertEqual(report["errors"][0]["cause"],"unclassified_needs_human_review")

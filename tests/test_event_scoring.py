"""Scoring faults that can otherwise make operational accuracy look too good."""
import unittest
from coffee_ops.event_evaluation import evaluate_events


def event(seconds,kind="person_entered",**extra):
    return {"seconds":seconds,"kind":kind,"camera_id":"shop","line_id":"door",**extra}


class EventScoringTests(unittest.TestCase):
    def test_global_one_to_one_assignment_is_order_independent(self):
        gt={"events":[event(0),event(1.4)],"event_tolerance_seconds":1}
        predicted=[event(.5),event(0)]
        for rows in [predicted,list(reversed(predicted))]:
            r=evaluate_events(gt,{"events":rows})
            self.assertEqual(r["tp"],2)
            self.assertEqual(r["event_f1"],1)

    def test_camera_and_line_scopes_cannot_match_each_other(self):
        gt={"events":[event(1)]}
        for wrong in [event(1,camera_id="other"),event(1,line_id="other"),event(1,kind="person_exited")]:
            result=evaluate_events(gt,{"events":[wrong]})
            self.assertEqual((result["tp"],result["fp"],result["fn"]),(0,1,1))

    def test_extra_prediction_is_false_positive_and_duplicate_id_is_reported(self):
        result=evaluate_events({"events":[event(1)],"duration_seconds":3600},
                               {"events":[event(1,event_id="e"),event(1,event_id="e")]})
        self.assertEqual(result["event_precision"],.5)
        self.assertEqual(result["duplicate_event_rate"],.5)
        self.assertEqual(result["false_events_per_hour"],1)
        self.assertEqual(result["signed_count_bias"],1)

    def test_event_specific_tolerance_and_timestamp_error(self):
        truth={"events":[event(1),event(10,"handover")],"event_tolerance_seconds":.1,
               "event_tolerances_seconds":{"handover":2}}
        r=evaluate_events(truth,{"events":[event(1.5),event(11,"handover")]})
        self.assertEqual(r["tp"],1)
        self.assertEqual(r["timestamp_mae_seconds"],1)
        self.assertEqual(r["per_class"]["handover"]["event_recall"],1)

    def test_unobservable_intervals_and_abstentions_are_excluded_from_exposure(self):
        truth={"events":[event(1),event(5)],"duration_seconds":10,
               "unscored_intervals":[{"start_seconds":4,"end_seconds":6}]}
        r=evaluate_events(truth,{"events":[event(1),event(5),event(8,status="uncertain")]})
        self.assertEqual(r["annotated_exposure_seconds"],8)
        self.assertEqual(r["tp"],1)
        self.assertEqual(r["fp"],0)
        self.assertEqual(r["excluded"]["truth_unscored"],1)
        self.assertAlmostEqual(r["abstention_rate"],1/3)

    def test_missing_annotations_do_not_mean_zero_ground_truth(self):
        with self.assertRaises(ValueError):evaluate_events({}, {"events":[]})
        r=evaluate_events({"events":[]},{"events":[event(1)]})
        self.assertEqual(r["fp"],1)
        self.assertIsNone(r["event_recall"])
        self.assertIsNone(r["percentage_error"])
        self.assertIsNone(r["false_events_per_hour"])

    def test_versioned_annotation_metadata_is_checked_before_scoring(self):
        with self.assertRaises(ValueError):evaluate_events({"schema_version":1,"events":[]},{})
        document={"schema_version":1,"clip_id":"a","camera_id":"shop","recording_group":"day-1",
                  "annotation_version":"1","time_origin_utc":"2026-01-01T09:00:00Z","duration_seconds":10,
                  "scored_event_kinds":["person_entered","person_exited"],"events":[]}
        self.assertEqual(evaluate_events(document,{})["absolute_error"],0)
        for version in [True,2]:
            with self.assertRaises(ValueError):evaluate_events(dict(document,schema_version=version),{})
        with self.assertRaises(ValueError):evaluate_events(document,dict(document,clip_id="other"))

    def test_legacy_camera_inference_is_allowed_only_when_unambiguous(self):
        legacy={"events":[{"kind":"person_entered","seconds":1,"line_id":"door"}]}
        self.assertEqual(evaluate_events(legacy,{"events":[event(1)]})["tp"],1)
        with self.assertRaises(ValueError):
            evaluate_events(legacy,{"events":[event(1),event(1,camera_id="other")]})

    def test_uncertain_ground_truth_must_not_become_negative_scored_time(self):
        with self.assertRaisesRegex(ValueError,"unscored interval"):
            evaluate_events({"events":[event(1,status="unobservable")]},{"events":[event(1)]})

    def test_unannotated_event_kinds_are_excluded_only_by_explicit_task_scope(self):
        truth={"events":[event(1)],"scored_event_kinds":["person_entered","person_exited"]}
        r=evaluate_events(truth,{"events":[event(1),event(2,"person_zone_entered")]})
        self.assertEqual(r["tp"],1)
        self.assertEqual(r["fp"],0)
        self.assertEqual(r["excluded"]["predictions_outside_task"],1)

    def test_invalid_times_confidence_intervals_and_capacity_fail_explicitly(self):
        for wrong in [event(float("nan")),event(-1),event(10),event(True),event(1,confidence=2)]:
            with self.assertRaises(ValueError):evaluate_events({"events":[],"duration_seconds":10},{"events":[wrong]})
        with self.assertRaises(ValueError):
            evaluate_events({"events":[],"duration_seconds":10,"unscored_intervals":[
                {"start_seconds":1,"end_seconds":5},{"start_seconds":4,"end_seconds":6}]},{})
        with self.assertRaisesRegex(ValueError,"capacity"):
            evaluate_events({"events":[event(1)]*1500},{"events":[event(1)]*1500})

import datetime
import unittest

from shusha.models.scheduler import BandwidthScheduler, ScheduleRule


class TestBandwidthScheduler(unittest.TestCase):
    def test_rule_active_time(self):
        rule = ScheduleRule(
            name="Work Hours",
            enabled=True,
            start_hour=9,
            start_minute=0,
            end_hour=17,
            end_minute=0,
            days_of_week=[0, 1, 2, 3, 4],  # Mon-Fri
            max_download_limit="1M",
            max_upload_limit="256K",
        )

        # Active case: Monday 12:30
        monday_noon = datetime.datetime(2026, 8, 24, 12, 30)  # Monday
        self.assertTrue(rule.is_active(monday_noon))

        # Inactive time case: Monday 20:00
        monday_night = datetime.datetime(2026, 8, 24, 20, 0)
        self.assertFalse(rule.is_active(monday_night))

        # Inactive day case: Sunday 12:30
        sunday_noon = datetime.datetime(2026, 8, 23, 12, 30)
        self.assertFalse(rule.is_active(sunday_noon))

    def test_scheduler_evaluation_and_serialization(self):
        scheduler = BandwidthScheduler()
        rule = ScheduleRule(
            name="Night Unlimited",
            enabled=True,
            start_hour=0,
            start_minute=0,
            end_hour=23,
            end_minute=59,
            days_of_week=[0, 1, 2, 3, 4, 5, 6],
            max_download_limit="10M",
            max_upload_limit="2M",
        )
        scheduler.add_rule(rule)

        limits = scheduler.evaluate()
        self.assertEqual(limits, ("10M", "2M"))

        dict_list = scheduler.to_dict_list()
        self.assertEqual(len(dict_list), 1)
        self.assertEqual(dict_list[0]["name"], "Night Unlimited")

        # Roundtrip deserialization
        restored = BandwidthScheduler.from_dict_list(dict_list)
        self.assertEqual(len(restored.rules), 1)
        self.assertEqual(restored.rules[0].name, "Night Unlimited")

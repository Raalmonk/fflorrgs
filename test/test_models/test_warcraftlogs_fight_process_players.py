import unittest
from unittest import mock
import datetime
from lorgs.models.warcraftlogs_fight import Fight
from lorgs.models.warcraftlogs_report import Report
from lorgs.clients.wcl.models.report_summary import ReportSummary, CompositionEntry, PlayerTotal, CompositionEntrySpec

# Rebuild models to resolve forward references
Fight.model_rebuild()
Report.model_rebuild()

class TestFightProcessPlayers(unittest.TestCase):
    def setUp(self):
        self.fight = Fight(fight_id=1, start_time=datetime.datetime.fromtimestamp(0), duration=10000)
        self.fight.report = mock.MagicMock(report_id="test")

        # Mock WowSpec.get
        self.spec_patch = mock.patch("lorgs.models.wow_spec.WowSpec.get")
        self.spec_mock = self.spec_patch.start()

    def tearDown(self):
        self.spec_patch.stop()

    def test_process_players_healer_uses_damage(self):
        # Setup Healer Spec
        healer_spec_mock = mock.MagicMock()
        healer_spec_mock.role.code = "heal"
        healer_spec_mock.full_name_slug = "white-mage"
        healer_spec_mock.wow_class.name_slug = "white-mage"

        # Setup DPS Spec
        dps_spec_mock = mock.MagicMock()
        dps_spec_mock.role.code = "dps"
        dps_spec_mock.full_name_slug = "samurai"
        dps_spec_mock.wow_class.name_slug = "samurai"

        def get_spec(name_slug_cap=None, wow_class__name_slug_cap=None, **kwargs):
            if name_slug_cap == "WhiteMage":
                return healer_spec_mock
            return dps_spec_mock

        self.spec_mock.side_effect = get_spec

        # Create Summary Data
        # Healer: 1000 Healing, 500 Damage
        # DPS: 0 Healing, 2000 Damage

        summary_data = ReportSummary(
            totalTime=10000,
            damageDone=[
                PlayerTotal(id=1, name="Healer", type="WhiteMage", total=5000), # 500 DPS
                PlayerTotal(id=2, name="DPS", type="Samurai", total=20000), # 2000 DPS
            ],
            healingDone=[
                PlayerTotal(id=1, name="Healer", type="WhiteMage", total=10000), # 1000 HPS
                PlayerTotal(id=2, name="DPS", type="Samurai", total=0),
            ],
            composition=[
                CompositionEntry(id=1, name="Healer", type="WhiteMage", specs=[CompositionEntrySpec(spec="WhiteMage")]),
                CompositionEntry(id=2, name="DPS", type="Samurai", specs=[CompositionEntrySpec(spec="Samurai")]),
            ]
        )

        self.fight.process_players(summary_data)

        # Verify Healer
        healer = self.fight.get_player(name="Healer")
        # Current behavior (before fix): Uses Healing (10000 / 10 = 1000)
        # Desired behavior (after fix): Uses Damage (5000 / 10 = 500)

        # Verify DPS
        dps = self.fight.get_player(name="DPS")
        # Should be 20000 / 10 = 2000

        # Print for manual verification
        print(f"Healer Total: {healer.total}")
        print(f"DPS Total: {dps.total}")

        # Assert DPS is always correct
        self.assertEqual(dps.total, 2000)

        # Assert Healer uses Damage (This assertion is expected to FAIL before the fix, or PASS after the fix)
        # Since I'm writing this test to verify the fix, I'll assert the DESIRED behavior.
        self.assertEqual(healer.total, 500)

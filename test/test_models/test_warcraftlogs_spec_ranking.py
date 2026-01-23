# IMPORT STANDARD LIBRARIES
import unittest
from unittest import mock


# IMPORT LOCAL LIBRARIES
from lorgs.models.warcraftlogs_ranking import SpecRanking
from ..helpers import load_fixture


class TestSpecRanking(unittest.IsolatedAsyncioTestCase):


    def setUp(self) -> None:
        self.spec_ranking = SpecRanking(spec_slug="test_spec", boss_slug="test_boss", metric="metric")

        self.boss_patch = mock.patch("lorgs.models.raid_boss.RaidBoss.get")
        self.boss_mock = self.boss_patch.start()
        self.boss_mock.return_value = mock.MagicMock(id=2048)


        self.spec_patch = mock.patch("lorgs.models.wow_spec.WowSpec.get")
        self.spec_mock = self.spec_patch.start()
        self.spec_mock.return_value = mock.MagicMock(**{
            "wow_class.name_slug_cap": "ClassName",
            "name_slug_cap": "SpecName",
            "role.metric": "metric",
        })

    def tearDown(self) -> None:
        self.boss_patch.stop()
        self.spec_patch.stop()


    def test__get_query(self):
        query = self.spec_ranking.get_query()

        assert 'className: "ClassName"' in query
        assert 'specName: "SpecName"' in query
        assert 'metric: metric' in query
        assert 'difficulty: 101' in query
        assert 'cn:' not in query
        assert 'serverRegion: "CN"' not in query

    def test__get_query_cn(self):
        query = self.spec_ranking.get_query(region="CN")
        assert 'serverRegion: "CN"' in query
        assert 'cn:' not in query

    @mock.patch("lorgs.models.warcraftlogs_ranking.SpecRanking.process_query_result")
    async def test__load_rankings(self, mock_process):
        # mock client
        client_mock = mock.AsyncMock()
        client_mock.query.return_value = {
            "worldData": {
                "encounter": {
                    "characterRankings": "DATA"
                }
            }
        }

        with mock.patch("lorgs.clients.wcl.WarcraftlogsClient.get_instance", return_value=client_mock):
             await self.spec_ranking.load_rankings()

        # check calls
        assert client_mock.query.call_count == 2

        # Check args
        calls = client_mock.query.call_args_list
        # call 1: Global
        assert "serverRegion" not in calls[0][0][0] # query string
        assert "region" not in calls[0].kwargs

        # call 2: CN
        assert "serverRegion" in calls[1][0][0] # query string
        assert calls[1].kwargs.get("region") == "CN"

        # Check Merge
        mock_process.assert_called_once()
        call_args = mock_process.call_args

        # we expect the result to have "cn": "DATA" merged in
        result = call_args.kwargs
        cn_data = result["worldData"]["encounter"]["cn"]
        assert cn_data == "DATA"

    def test__process_query_result_one(self):

        data = {
            "worldData": {
                "encounter": {
                    "characterRankings": {
                        "rankings": [
                            {
                                "name": "PlayerName",
                                "class": "ClassName",
                                "spec": "SpecName",
							    "amount": 123456,
							    "duration": 5432,
							    "startTime": 1634544096374,
							    "covenantID": 2,
							    "soulbindID": 9,
							    "report": {
								    "code": "REPORT_CODE",
								    "fightID": 5,
								    "startTime": 1634543354962
							    }
                            }
                        ]
                    }
                }
            }
        }
        self.spec_ranking.process_query_result(**data)

        assert len(self.spec_ranking.reports) == 1

        report = self.spec_ranking.reports[0]
        assert report.report_id == "REPORT_CODE"

        fight = report.fights[0]
        assert fight.fight_id == 5
        assert fight.duration == 5432

        player = fight.players[0]
        assert player.name == "PlayerName"
        assert player.total == 123456
        assert player.casts == []

    def test__process_query_result_fixture(self):

        data = load_fixture("spec_rankings_1.json")
        # data = data.get("data")

        self.spec_ranking.process_query_result(**data)

        # Global limit is 5
        assert len(self.spec_ranking.reports) == 5

"""Models for Top Rankings for a given Spec."""

from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import datetime
import textwrap
import typing
from typing import Dict, Tuple, ClassVar

# IMPORT THIRD PARTY LIBRARIES
import pydantic  # [新增] 引入 pydantic 以使用 PrivateAttr

# IMPORT LOCAL LIBRARIES
from lorgs import utils
from lorgs.clients import wcl
from lorgs.logger import logger
from lorgs.models import warcraftlogs_base
from lorgs.models.base.s3 import S3Model
from lorgs.models.raid_boss import RaidBoss
from lorgs.models.warcraftlogs_boss import Boss
from lorgs.models.warcraftlogs_fight import Fight
from lorgs.models.warcraftlogs_player import Player
from lorgs.models.warcraftlogs_report import Report
from lorgs.models.wow_spec import WowSpec


# Map Difficulty Names to Integers used in WCL
DIFFICULTY_IDS = {
    "normal": 100,
    "heroic": 101,
    "mythic": 101,
    "savage": 101,
    "extreme": 102,
    "ultimate": 103,
}


class SpecRanking(S3Model, warcraftlogs_base.wclclient_mixin):
    # Fields
    spec_slug: str
    boss_slug: str
    difficulty: str = "mythic"
    metric: str = "rdps"
    reports: list[Report] = []

    updated: datetime.datetime = datetime.datetime.min
    dirty: bool = False
    
    # [修复] 使用 PrivateAttr 防止该字段被序列化到 JSON 中
    # 这一步解决了 "keys must be str... not tuple" 的报错
    _official_dps_cache: Dict[Tuple[int, str], float] = pydantic.PrivateAttr(default_factory=dict)

    # Config
    key: typing.ClassVar[str] = "{spec_slug}/{boss_slug}__{difficulty}__{metric}"

    def post_init(self) -> None:
        for report in self.reports:
            report.post_init()

    ##########################
    # Attributes
    #
    @property
    def spec(self) -> WowSpec:
        return WowSpec.get(full_name_slug=self.spec_slug)  # type: ignore

    @property
    def boss(self) -> RaidBoss:
        return RaidBoss.get(full_name_slug=self.boss_slug)  # type: ignore

    @property
    def fights(self) -> list[Fight]:
        return utils.flatten(report.fights for report in self.reports)

    @property
    def players(self) -> list[Player]:
        return utils.flatten(fight.players for fight in self.fights)

    ##########################
    # Methods
    #
    @staticmethod
    def sort_reports(reports: list[Report]) -> list[Report]:
        """Sort the reports in place by the highest dps player."""
        def get_total(report: Report) -> float:
            top = 0.0
            for fight in report.fights:
                for player in fight.players:
                    top = max(top, player.total)
            return top
        return sorted(reports, key=get_total, reverse=True)

    ############################################################################
    # Query: Rankings
    #
    def get_query(self) -> str:
        """Return the Query to load the rankings for this Spec & Boss."""
        difficulty_id = DIFFICULTY_IDS.get(self.difficulty) or 101
        real_class_name = "Global"
        cn_class_name = "Global"
        spec_name = self.spec.name_slug_cap

        def build_rankings_query(class_name_arg: str, extra_args: str = ""):
            return f"""
                characterRankings(
                    className: "{class_name_arg}"
                    specName: "{spec_name}"
                    metric: {self.metric}
                    difficulty: {difficulty_id}
                    includeCombatantInfo: true
                    {extra_args}
                )
            """

        return textwrap.dedent(
            f"""\
        worldData
        {{
            encounter(id: {self.boss.id})
            {{
                global: {build_rankings_query(real_class_name)}
                cn: {build_rankings_query(cn_class_name, 'partition: 3, serverRegion: "CN"')}
            }}
        }}
        """
        )

    @utils.as_list
    def get_old_reports(self) -> typing.Generator[tuple[str, int, str], None, None]:
        for report in self.reports:
            for fight in report.fights:
                for player in fight.players:
                    key = (report.report_id, fight.fight_id, player.name)
                    yield key

    def add_new_fight(self, ranking_data: wcl.CharacterRanking) -> None:
        report_data = ranking_data.report
        if not report_data:
            return
        if ranking_data.hidden:
            return

        # Player
        player = Player(
            name=ranking_data.name,
            total=ranking_data.amount,
            spec_slug=self.spec_slug,
        )

        # Fight
        fight = Fight(
            fight_id=report_data.fightID,
            start_time=ranking_data.startTime,
            duration=ranking_data.duration,
            players=[player],
        )

        # Parse combatantInfo to add partners
        if ranking_data.combatantInfo:
            for combatant in ranking_data.combatantInfo:
                name = combatant.get("name")
                if name == player.name:
                    continue

                spec_name = combatant.get("spec")
                class_name = combatant.get("type")

                if spec_name and spec_name.lower() in ("dps", "healer", "tank"):
                     spec_name = class_name

                spec = WowSpec.get(name_slug_cap=spec_name, wow_class__name_slug_cap=class_name)
                if not spec:
                    spec = WowSpec.get(name_slug_cap=spec_name)
                if not spec:
                    continue

                p = Player(
                    source_id=combatant.get("id"),
                    name=name,
                    spec_slug=spec.full_name_slug,
                    total=0,
                )
                p.fight = fight
                fight.players.append(p)

        fight.composition = [p.spec_slug for p in fight.players]
        
        report = Report(
            report_id=report_data.code,
            start_time=report_data.startTime,
            fights=[fight],
            region=ranking_data.server.region,
        )
        self.reports.append(report)

    def add_new_fights(self, rankings: list[wcl.CharacterRanking]):
        old_reports = self.get_old_reports()
        for ranking_data in rankings:
            report_data = ranking_data.report
            key = (report_data.code, report_data.fightID, ranking_data.name)
            if key in old_reports:
                continue
            self.add_new_fight(ranking_data)

    def process_query_result(self, **query_result: typing.Any):
        """Process the Ranking Results."""
        encounter_data = query_result.get("worldData", {}).get("encounter", {})

        global_data = encounter_data.get("global", {})
        global_rankings = wcl.CharacterRankings(**global_data).rankings 

        cn_data = encounter_data.get("cn", {})
        cn_rankings = wcl.CharacterRankings(**cn_data).rankings

        rankings = global_rankings + cn_rankings
        
        # 填充私有缓存
        self._official_dps_cache = {}
        
        def normalize_name(n):
            return n.split("-")[0].strip() if "-" in n else n.strip()

        for r in rankings:
            simple_key = (r.report.fightID, normalize_name(r.name))
            self._official_dps_cache[simple_key] = r.amount
            
            raw_key = (r.report.fightID, r.name)
            self._official_dps_cache[raw_key] = r.amount

        self.add_new_fights(rankings)
        self.post_init()

    async def load_rankings(self) -> None:
        """Fetch the current Ranking Data"""
        query = self.get_query()
        result = await self.client.query(query)
        self.process_query_result(**result)

    ############################################################################
    # Query: Fights
    #
    async def load_actors(self) -> None:
        """Load the Casts for all missing fights."""
        actors_to_load = [p for p in self.players if p.spec_slug == self.spec_slug]
        for i, fight in enumerate(self.fights):
            if not fight.boss:
                fight.boss = Boss(boss_slug=self.boss_slug)
                fight.boss.fight = fight
            if i == 0:
                fight.boss.query_mode = fight.boss.QueryModes.ALL
            else:
                fight.boss.query_mode = fight.boss.QueryModes.PHASES
            actors_to_load.append(fight.boss)

        actors_to_load = [actor for actor in actors_to_load if actor and not actor.casts]
        logger.info(f"load {len(actors_to_load)} players/bosses")
        if not actors_to_load:
            return
        await self.load_many(actors_to_load, raise_errors=False)

    ############################################################################
    # Query: Both
    #
    async def load(self, limit=50, clear_old=False) -> None:
        """Get Top Ranks for a given boss and spec."""
        logger.info(f"{self.boss.name} vs. {self.spec.name} {self.spec.wow_class.name} START | limit={limit} | clear_old={clear_old}")

        if clear_old:
            self.reports = []
            self._official_dps_cache = {}

        await self.load_rankings()
        self.reports = self.sort_reports(self.reports)

        limit = limit or -1
        self.reports = self.reports[:limit]

        fights_missing_comp = [f for f in self.fights if len(f.players) <= 1]
        if fights_missing_comp:
            logger.info(f"[Fallback] Fetching Composition for {len(fights_missing_comp)} fights...")
            await self.load_many(fights_missing_comp, raise_errors=False)

        await self.load_actors()
        
        # [Final Fix] 使用私有缓存进行覆盖
        def normalize_name(n):
            return n.split("-")[0].strip() if "-" in n else n.strip()

        restore_count_final = 0
        for report in self.reports:
            for fight in report.fights:
                for player in fight.players:
                    key_simple = (fight.fight_id, normalize_name(player.name))
                    key_raw = (fight.fight_id, player.name)
                    
                    # 读取私有变量
                    official_val = self._official_dps_cache.get(key_simple) or self._official_dps_cache.get(key_raw)
                    
                    if official_val is not None:
                        if abs(player.total - official_val) > 0.1: 
                            player.total = official_val
                            restore_count_final += 1
                            if "引力" in player.name or "偷心" in player.name:
                                logger.info(f"[DPS Final Fix] RESTORING {player.name}: {player.total} -> {official_val}")
        
        if restore_count_final > 0:
            logger.info(f"[DPS Final Fix] Corrected DPS for {restore_count_final} players to strictly match Leaderboard.")
        
        logger.info("done")
        self.updated = datetime.datetime.now(datetime.timezone.utc)
        self.dirty = False

from lorgs.models.warcraftlogs_report import Report
SpecRanking.model_rebuild()
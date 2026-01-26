"""Models for Top Rankings for a given Spec."""

from __future__ import annotations

# IMPORT STANDARD LIBRARIES
import datetime
import textwrap
import typing
from typing import Optional

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
    "heroic": 101,  # savage
    "mythic": 101,  # savage
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
    def _normalize_name(name: str) -> str:
        """Helper: Normalize player name by removing server suffix."""
        if not name:
            return ""
        # Split by '-' and take the first part (Name), strip whitespace
        return name.split("-")[0].strip()

    @staticmethod
    def sort_reports(reports: list[Report]) -> list[Report]:
        """Sort the reports in place by the highest dps player."""

        def get_total(report: Report) -> float:
            top = 0.0
            for fight in report.fights:
                # 只有主角 (index 0) 的 DPS 算数，避免被高 DPS 的配角干扰排序
                if fight.players:
                    top = max(top, fight.players[0].total)
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

        # 2. 定义查询构建函数 (支持传入不同的 class_name)
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

        # 3. 组合查询：Global 用具体名，CN 用 "Global"
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
        """Return a list of unique keys to identify existing reports."""
        for report in self.reports:
            for fight in report.fights:
                for player in fight.players:
                    key = (report.report_id, fight.fight_id, player.name)
                    yield key

    def add_new_fight(self, ranking_data: wcl.CharacterRanking) -> None:
        report_data = ranking_data.report

        if not report_data:
            return

        # skip hidden reports
        if ranking_data.hidden:
            return

        ################
        # Player (Primary Ranker - ALWAYS Index 0)
        player = Player(
            name=ranking_data.name,
            total=ranking_data.amount,
            spec_slug=self.spec_slug,
        )

        ################
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
                # Combatant is a dict
                name = combatant.get("name")
                if name == player.name:
                    continue

                spec_name = combatant.get("spec")
                class_name = combatant.get("type")

                if spec_name and spec_name.lower() in ("dps", "healer", "tank"):
                     spec_name = class_name

                # 1. Try Strict Lookup (Class + Spec)
                spec = WowSpec.get(name_slug_cap=spec_name, wow_class__name_slug_cap=class_name)

                # 2. FIX: Fallback Lookup (Spec only) for FF14 compatibility
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

        # Populate the composition list with spec slugs
        fight.composition = [p.spec_slug for p in fight.players]

        ################
        # Report
        report = Report(
            report_id=report_data.code,
            start_time=report_data.startTime,
            fights=[fight],
            region=ranking_data.server.region,
        )
        self.reports.append(report)

    def add_new_fights(self, rankings: list[wcl.CharacterRanking]):
        """Add new Fights."""
        old_reports = self.get_old_reports()

        for ranking_data in rankings:
            report_data = ranking_data.report

            ################
            # check if already in the list
            key = (report_data.code, report_data.fightID, ranking_data.name)
            if key in old_reports:
                continue

            self.add_new_fight(ranking_data)

    def process_query_result(self, **query_result: typing.Any):
        """Process the Ranking Results."""
        # unwrap data
        encounter_data = query_result.get("worldData", {}).get("encounter", {})

        # 1. Global (Load ALL)
        global_data = encounter_data.get("global", {})
        global_rankings = wcl.CharacterRankings(**global_data).rankings

        # 2. CN (Load ALL)
        cn_data = encounter_data.get("cn", {})
        cn_rankings = wcl.CharacterRankings(**cn_data).rankings

        # Log check
        if cn_rankings:
            logger.info(f"[CN Data Check] First CN Player: {cn_rankings[0].name}")

        # Merge
        rankings = global_rankings + cn_rankings
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
        
        # [优化] 只加载主角的技能数据
        actors_to_load = [p for p in self.players if p.spec_slug == self.spec_slug]

        # 添加 Boss
        for i, fight in enumerate(self.fights):
            if not fight.boss:
                fight.boss = Boss(boss_slug=self.boss_slug)
                fight.boss.fight = fight

            if i == 0:
                fight.boss.query_mode = fight.boss.QueryModes.ALL
            else:
                fight.boss.query_mode = fight.boss.QueryModes.PHASES

            actors_to_load.append(fight.boss)

        # 过滤掉已经加载过的
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
        logger.info(f"--- [v3] LOADING WITH HIGHLANDER FIX (Censor Impostors) ---") 
        logger.info(f"{self.boss.name} vs. {self.spec.name} {self.spec.wow_class.name} START | limit={limit} | clear_old={clear_old}")

        if clear_old:
            self.reports = []

        # 1. Load Rankings (这里拿到的数据是绝对正确的)
        await self.load_rankings()
        self.reports = self.sort_reports(self.reports)

        # ============================================================
        # [NEW] Snapshot Official DPS (只记录主角的正确数值)
        # ============================================================
        official_dps_map = {}
        for report in self.reports:
            for fight in report.fights:
                if fight.players:
                    # 规则：列表第一个人永远是主角 (Ranker)
                    p = fight.players[0]
                    clean_name = SpecRanking._normalize_name(p.name)
                    key = (fight.fight_id, clean_name)
                    official_dps_map[key] = p.total
        # ============================================================

        # 2. Apply Limit
        limit = limit or -1
        self.reports = self.reports[:limit]

        # 3. Fetch Details (这一步会污染数据，因为WCL详情里的DPS是错的)
        fights_missing_comp = [f for f in self.fights if len(f.players) <= 1]
        
        if fights_missing_comp:
            logger.info(f"[Fallback] Fetching Composition for {len(fights_missing_comp)} fights...")
            await self.load_many(fights_missing_comp, raise_errors=False)

            # ============================================================
            # [NEW] 数据清洗 (Cleaning)
            # ============================================================
            restore_count = 0
            censor_count = 0
            
            for fight in self.fights:
                if not fight.players:
                    continue
                
                # 1. 认领主角 (First player is ALWAYS the Ranker)
                ranker = fight.players[0]
                
                # 2. 修复主角数据 (如果被污染了，强制恢复成榜单值)
                clean_name = SpecRanking._normalize_name(ranker.name)
                key = (fight.fight_id, clean_name)
                official_val = official_dps_map.get(key)
                
                if official_val is not None:
                    # 只要不一致就恢复
                    if abs(ranker.total - official_val) > 1.0:
                        ranker.total = official_val
                        restore_count += 1
                
                # 3. 封杀配角 (Censor Teammates)
                # 任何出现在队友列表里的同职业玩家，都必须闭嘴 (DPS=0)
                # 这样前端在排序/显示时，就不会把配角当成高伤害的主角显示出来
                for teammate in fight.players[1:]:
                    if teammate.spec_slug == self.spec_slug:
                        if teammate.total > 0:
                            teammate.total = 0 # 强制归零
                            censor_count += 1

            logger.info(f"[DPS Fix] Restored {restore_count} Rankers | Censored {censor_count} Impostors (Teammates).")
            # ============================================================

        # 4. Load Spells
        await self.load_actors()
        
        logger.info("done")

        self.updated = datetime.datetime.now(datetime.timezone.utc)
        self.dirty = False
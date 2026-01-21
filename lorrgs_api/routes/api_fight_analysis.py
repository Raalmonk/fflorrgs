"""API Routes for detailed Fight Analysis."""
from __future__ import annotations

# IMPORT THIRD PARTY LIBRARIES
import fastapi

# IMPORT LOCAL LIBRARIES
from lorgs.models.warcraftlogs_report import Report

router = fastapi.APIRouter()

@router.get("/fight_analysis/{report_id}/{fight_id}")
async def get_fight_analysis(report_id: str, fight_id: int, spec: str | None = None):
    """获取指定战斗的详细施法时间轴数据。
    
    Args:
        report_id (str): WCL/FFLogs 报告 ID
        fight_id (int): 战斗 ID
        spec (str, optional): 职业过滤 (例如 "Pictomancer" 或 "redmage-redmage")
    """
    
    # 1. 初始化并加载报告元数据
    report = Report(report_id=report_id)
    # 加载 Report MasterData (战斗列表等)
    await report.load()
    
    # 2. 获取特定战斗
    fight = report.get_fight(fight_id=fight_id)
    if not fight:
        return fastapi.Response(content="Fight not found", status_code=404)
        
    # 3. 加载战斗摘要 (获取玩家列表)
    await fight.load()
    
    # 4. 确定要加载哪些玩家
    players_to_load = fight.players
    if spec:
        players_to_load = [p for p in fight.players if p.spec_slug == spec]
        
    if not players_to_load:
        return fastapi.Response(content=f"No players found for spec: {spec}", status_code=404)

    # 5. 并行加载选定玩家的施法数据
    # 只有当 casts 为空时才去加载，避免重复
    for player in players_to_load:
        if not player.casts:
            await player.load()

    # 6. 返回数据
    # 利用 fight.as_dict()，它会自动包含 players 和里面的 casts
    loaded_player_ids = [p.source_id for p in players_to_load]
    return fight.as_dict(player_ids=loaded_player_ids)
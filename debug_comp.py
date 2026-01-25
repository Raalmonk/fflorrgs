# debug_comp.py
import asyncio
import os

# 确保能找到 lorgs 模块
import sys
sys.path.append(os.getcwd())

from lorgs.models.warcraftlogs_comp_ranking import CompRanking

async def main():
    boss_slug = "vamp-fatale"  # 或者其他你想测试的 Boss Slug
    print(f"--- Starting Debug for Boss: {boss_slug} ---")
    
    # 1. 获取或创建 CompRanking 对象
    ranking = CompRanking.get_or_create(boss_slug=boss_slug)
    
    # 2. 强制加载数据 (这会触发 Fight.load -> process_query_result -> process_players)
    # limit=5 限制数量，加快调试速度
    # clear_old=True 清除旧数据，确保重新抓取
    await ranking.load(limit=5, clear_old=True)
    
    print("--- Debug Finished ---")
    
    # 打印结果检查
    if ranking.reports:
        first_fight = ranking.reports[0].fights[0]
        print(f"First Fight Players Count: {len(first_fight.players)}")
        print(f"First Fight Composition: {first_fight.composition}")
    else:
        print("No reports loaded.")

if __name__ == "__main__":
    asyncio.run(main())
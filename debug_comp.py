import asyncio
import os
import sys

# 1. 配置环境（必须在导入 lorgs 模块之前）
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ["AWS_SECURITY_TOKEN"] = "testing"
os.environ["AWS_SESSION_TOKEN"] = "testing"
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

os.environ["WCL_CLIENT_ID"] = "a0e16bba-fba8-432d-a317-4a6a83d98728"
os.environ["WCL_CLIENT_SECRET"] = "Rowpl4stVguifS4YJbzow1HCjh1g2uNuGNaFYRPk"

# 2. 设置路径
sys.path.append(os.getcwd())

print(">>> [INIT] Environment setup complete.")

# 3. 导入核心模型
try:
    from lorgs.models.raid_boss import RaidBoss
    from lorgs.models.warcraftlogs_comp_ranking import CompRanking
    print(">>> [INIT] Core models imported.")
except ImportError as e:
    print(f"!!! [ERROR] Failed to import core models: {e}")
    sys.exit(1)

# 4. [关键步骤] 显式导入数据
# 我们直接导入定义了 Vamp Fatale 的具体文件，确保代码被执行
print(">>> [DATA] Attempting to load Boss Data...")
try:
    # 强制导入 Arcadion Heavyweight 团本数据
    import lorgs.data.expansions.dawntrail.raids.arcadion_heavyweight
    print(">>> [DATA] Expansion module imported successfully.")
except ImportError as e:
    print(f"!!! [ERROR] Failed to import data module: {e}")
    sys.exit(1)

# 5. [诊断] 检查 Boss 是否存在
target_slug = "vamp-fatale"
boss = RaidBoss.get(full_name_slug=target_slug)

if not boss:
    print(f"\n!!! [CRITICAL FAILURE] Boss lookup failed for '{target_slug}'")
    print("Debugging Info:")
    # 尝试列出所有已知的 RaidBoss (如果 store 存在)
    # 注意: 这里假设 RaidBoss 使用的是内存存储，我们可以尝试打印存储内容
    try:
        # 这是一个猜测，基于常见的 lorgs 架构，如果失败会进入 except
        all_bosses = [b.full_name_slug for b in RaidBoss.store.values()] if hasattr(RaidBoss, 'store') else "Unknown storage"
        print(f"Available Bosses: {all_bosses}")
    except Exception as e:
        print(f"Could not list bosses: {e}")
    sys.exit(1)
else:
    print(f">>> [CHECK] Boss Found: {boss.name} (ID: {boss.id})")


# 6. 开始抓取业务逻辑
async def main():
    print(f"\n--- Starting Debug for Boss: {boss.name} ---")
    
    # 获取对象
    ranking = CompRanking.get_or_create(boss_slug=target_slug)
    
    print(">>> [ACTION] Calling ranking.load()...")
    # clear_old=True 强制重新抓取，这会触发 fight.py 里的 print
    try:
        await ranking.load(limit=5, clear_old=True)
        print(">>> [ACTION] ranking.load() finished.")
    except Exception as e:
        print(f"!!! [ERROR] Error during ranking.load(): {e}")
        import traceback
        traceback.print_exc()
        return

    # 7. 打印结果
    if ranking.reports:
        print(f"\n>>> [RESULT] Successfully loaded {len(ranking.reports)} reports.")
        first_report = ranking.reports[0]
        if first_report.fights:
            first_fight = first_report.fights[0]
            print(f"   - Report ID: {first_report.report_id}")
            print(f"   - Fight ID: {first_fight.fight_id}")
            print(f"   - Players Count: {len(first_fight.players)}")
            print(f"   - Composition: {first_fight.composition}")
            
            # 如果 Players Count 是 0，我们需要看 Composition 数据源
            if not first_fight.players:
                print("\n   [ANALYSIS] Players list is empty. Check logs above for '[DEBUG]' messages from warcraftlogs_fight.py.")
        else:
            print("   - First report has no fights.")
    else:
        print(">>> [RESULT] No reports loaded.")

if __name__ == "__main__":
    asyncio.run(main())
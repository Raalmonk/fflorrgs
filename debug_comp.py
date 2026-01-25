import os
import sys

# 1. 确保能导入 lorgs
sys.path.append(os.getcwd())

# 2. 导入数据模块 (这会触发 Boss 的注册)
import lorgs.data 
from lorgs.models.raid_zone import RaidZone

# 3. 打印所有已注册的 Boss
print("--- Loaded Bosses ---")
found = False

# [修正点] 使用 .list() 获取所有内存中的 Zone 对象
zones = RaidZone.list()
print(f"DEBUG: Found {len(zones)} zones in memory.")

for zone in zones:
    print(f"\nZone: {zone.name} (ID: {zone.id})")
    for boss in zone.bosses:
        print(f"  - [{boss.id}] {boss.name} (Nick: {boss.nick}) -> Slug: {boss.full_name_slug}")
        # 检查 Nick 或者 Slug
        if boss.nick == "M12S P2" or "lindwurm-ii" in boss.full_name_slug:
            found = True

print("\n-------------------")
if found:
    print("✅ SUCCESS: M12S P2 is loaded in the backend!")
else:
    print("❌ FAILURE: M12S P2 is NOT loaded. Check your imports.")
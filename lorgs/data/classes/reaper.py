"""Define the Reaper Class and its Spec and Spells."""

# pylint: disable=line-too-long
# pylint: disable=bad-whitespace
# pylint: disable=wildcard-import
# pylint: disable=unused-wildcard-import
# fmt: off

# IMPORT LOCAL LIBRARIES
from lorgs.data.constants import *
from lorgs.data.roles import *
from lorgs.models.wow_class import WowClass
from lorgs.models.wow_spec import WowSpec
from lorgs.models.wow_spell import SpellTag


################################################################################
# Class
#
REAPER = WowClass(id=39, name="Reaper", color="#965A90")

################################################################################
# Specs
#
REAPER_MAIN = WowSpec(role=MDPS, wow_class=REAPER, name="Reaper")


################################################################################
# Spells
#

# Burst / Cooldowns
REAPER_MAIN.add_spell(spell_id=24405, cooldown=120, duration=20, name="Arcane Circle", show=True,icon="Arcane_Circle.png", tags=[SpellTag.DAMAGE])
REAPER_MAIN.add_spell(spell_id=24394, cooldown=5, name="Enshroud", icon="Enshroud.png", show=True,tags=[SpellTag.DAMAGE])
REAPER_MAIN.add_spell(spell_id=24393, cooldown=60,name="Gluttony", icon="Gluttony.png",show=True, tags=[SpellTag.DAMAGE])

REAPER_MAIN.add_spell(spell_id=24380, cooldown=30, name="Soul Slice", icon="Soul_Slice.png", show=False,tags=[SpellTag.DAMAGE])


REAPER_MAIN.add_spell(spell_id=7546, cooldown=45, duration=10, name="True North", show=True,icon="True_North.png", tags=[SpellTag.DAMAGE])

# Self Mitigation
REAPER_MAIN.add_spell(spell_id=7541, cooldown=120, name="Second Wind", icon="Second_Wind.png",show=False, tags=[SpellTag.DEFENSIVE])
REAPER_MAIN.add_spell(spell_id=7542, cooldown=90, duration=20, name="Bloodbath", icon="Bloodbath.png",show=False, tags=[SpellTag.DEFENSIVE])


# Party Mitigation
REAPER_MAIN.add_spell(spell_id=7549, cooldown=90, duration=15, name="Feint", icon="Feint.png",show=True, tags=[SpellTag.RAID_CD])
REAPER_MAIN.add_spell(spell_id=24404, cooldown=30, name="Arcane Crest", icon="Arcane_Crest.png", show=False,tags=[SpellTag.RAID_CD])

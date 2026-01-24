"""Define the Machinist Class and its Spec and Spells."""

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
MACHINIST = WowClass(id=31, name="Machinist", color="#6EE1D6")

################################################################################
# Specs
#
MACHINIST_MAIN = WowSpec(role=RDPS, wow_class=MACHINIST, name="Machinist")


################################################################################
# Spells
#

# Burst / Cooldowns
MACHINIST_MAIN.add_spell(spell_id=16501, cooldown=6, duration=12, name="Automaton Queen", show=True, icon="Automaton_Queen.png", tags=[SpellTag.DAMAGE])
MACHINIST_MAIN.add_spell(spell_id=2876, cooldown=55, name="Reassemble", show=False, icon="Reassemble.png", tags=[SpellTag.DAMAGE])
MACHINIST_MAIN.add_spell(spell_id=17209, name="Hypercharge", show=True, icon="Hypercharge.png", tags=[SpellTag.DAMAGE])
MACHINIST_MAIN.add_spell(spell_id=7414, cooldown=120, name="Barrel Stabilizer", show=True, icon="Barrel_Stabilizer.png", tags=[SpellTag.DAMAGE])
MACHINIST_MAIN.add_spell(spell_id=2878, cooldown=120, name="Wildfire", show=False, icon="Wildfire.png", tags=[SpellTag.DAMAGE])
MACHINIST_MAIN.add_spell(spell_id=16498, cooldown=20, name="Drill", show=False, icon="Drill.png", tags=[SpellTag.DAMAGE])
MACHINIST_MAIN.add_spell(spell_id=16500, cooldown=40, name="Air Anchor", show=False, icon="Air_Anchor.png", tags=[SpellTag.DAMAGE])
MACHINIST_MAIN.add_spell(spell_id=25788, cooldown=60, name="Chain Saw", show=False, icon="Chain_Saw.png", tags=[SpellTag.DAMAGE])


# Removed duplicate Wildfire entry

# Self Mitigation
MACHINIST_MAIN.add_spell(spell_id=7541, cooldown=120, name="Second Wind", show=False, icon="Second_Wind.png", tags=[SpellTag.DEFENSIVE])


# Party Mitigation
MACHINIST_MAIN.add_spell(spell_id=16889, cooldown=90, duration=15, name="Tactician", show=True, icon="Tactician.png", tags=[SpellTag.RAID_CD])
MACHINIST_MAIN.add_spell(spell_id=2887, cooldown=120, duration=10, name="Dismantle", show=True, icon="Dismantle.png", tags=[SpellTag.RAID_CD])

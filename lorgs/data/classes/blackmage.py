"""Define the Black Mage Class and its Spec and Spells."""

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
BLACK_MAGE = WowClass(id=25, name="Black Mage", color="#A579D6")

################################################################################
# Specs
#
BLACK_MAGE_MAIN = WowSpec(role=RDPS, wow_class=BLACK_MAGE, name="Black Mage")


################################################################################
# Spells
#

# Burst / Cooldowns
BLACK_MAGE_MAIN.add_spell(spell_id=158, cooldown=100, name="Manafont", icon="Manafont.png", show=True, tags=[SpellTag.DAMAGE])
BLACK_MAGE_MAIN.add_spell(spell_id=3573, cooldown=120, duration=30, name="Ley Lines", icon="Ley_Lines.png", show=True, tags=[SpellTag.DAMAGE])
BLACK_MAGE_MAIN.add_spell(spell_id=7421, cooldown=60, name="Triplecast", icon="Triplecast.png", show=True, tags=[SpellTag.DAMAGE])
BLACK_MAGE_MAIN.add_spell(spell_id=7561, cooldown=40, duration=10, name="Swiftcast", icon="Swiftcast.png", show=False, tags=[SpellTag.DAMAGE])

BLACK_MAGE_MAIN.add_spell(spell_id=16507, cooldown=2.5, name="Xenoglossy", icon="Xenoglossy.png", show=True, tags=[SpellTag.DAMAGE])
BLACK_MAGE_MAIN.add_spell(spell_id=7422, cooldown=2.5, name="Foul", icon="Foul.png", show=False, tags=[SpellTag.DAMAGE])
BLACK_MAGE_MAIN.add_spell(spell_id=162, cooldown=2.5, name="Flare", icon="Flare.png", show=False, tags=[SpellTag.DAMAGE])
BLACK_MAGE_MAIN.add_spell(spell_id=36989, cooldown=0, name="Flare Star", icon="Flare_Star.png", show=False, tags=[SpellTag.DAMAGE])

BLACK_MAGE_MAIN.add_spell(spell_id=149, cooldown=5, name="Transpose", icon="Transpose.png", show=False, tags=[SpellTag.DAMAGE])
BLACK_MAGE_MAIN.add_spell(spell_id=25797, cooldown=0, name="Paradox", icon="Paradox.png", show=False, tags=[SpellTag.DAMAGE])

# Self Mitigation
BLACK_MAGE_MAIN.add_spell(spell_id=157, cooldown=120, name="Manaward", show=False, icon="Manaward.png", tags=[SpellTag.DEFENSIVE])

BLACK_MAGE_MAIN.add_spell(spell_id=7560, cooldown=90, duration=15, name="Addle", icon="Addle.png", tags=[SpellTag.RAID_CD])

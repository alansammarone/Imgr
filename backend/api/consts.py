"""Constants for mask generation and refinement."""

from .mask_refinement_service import FeatheringMethod

# Mask refinement configuration
FEATHER_METHOD = FeatheringMethod.EASE_OUT_POWER
FEATHER_WIDTH = 10  # pixels

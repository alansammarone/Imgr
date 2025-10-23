"""Mask generation service that orchestrates SAM and mask refinement."""

from typing import Dict, List

from PIL import Image

from .consts import FEATHER_METHOD, FEATHER_WIDTH
from .mask_refinement_service import apply_feathering
from .sam_service import get_sam_service


class MaskGenerationService:
    """Service for generating and refining masks."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def generate_masks(
        self, image: Image.Image, points: List[Dict[str, int]], labels: List[int]
    ) -> List[Dict[str, any]]:
        """
        Generate and refine masks for given image and points.

        Args:
            image: PIL Image (RGB)
            points: List of dicts with 'x' and 'y' keys
            labels: List of ints (1 for positive/foreground, 0 for negative/background)

        Returns:
            List of dicts containing:
                - mask: numpy float array (H, W) with values in [0, 1]
                - score: float confidence score
        """
        # Get raw masks from SAM service
        sam_service = get_sam_service()
        raw_results = sam_service.generate_masks(image, points, labels)

        # Apply feathering to each mask using configured method and width
        refined_results = []
        for result in raw_results:
            mask = result["mask"]
            score = result["score"]

            # Apply feathering with configured method and width from consts.py
            feathered_mask = apply_feathering(mask, FEATHER_METHOD, FEATHER_WIDTH)

            refined_results.append(
                {
                    "mask": feathered_mask,
                    "score": score,
                }
            )

        return refined_results


# Global singleton instance
_mask_generation_service = None


def get_mask_generation_service() -> MaskGenerationService:
    """Get or create the global mask generation service instance."""
    global _mask_generation_service
    if _mask_generation_service is None:
        _mask_generation_service = MaskGenerationService()
    return _mask_generation_service

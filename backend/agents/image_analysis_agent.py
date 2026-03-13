"""
Agent 3 — Image Analysis Agent
Analyzes uploaded product images using mock CLIP / Vision LLM logic.
Detects product defects, compares images with description,
and detects misleading listings.
"""
import logging
import hashlib
import random

logger = logging.getLogger("ecommerce_agent.agents.image_analysis")


class ImageAnalysisAgent:
    def run(
        self,
        image1_b64: str = None,
        image2_b64: str = None,
        product_description: str = "",
        product_name: str = "",
    ) -> dict:
        """
        Analyze product images for quality and listing match.
        Returns: {
            image_quality_score, image_listing_match,
            image_results[]
        }
        """
        logger.info("[ImageAnalysisAgent] Starting image analysis")

        image_results = []
        quality_scores = []

        for idx, img_b64 in enumerate([image1_b64, image2_b64], start=1):
            if not img_b64:
                continue

            # Deterministic scoring based on image data hash
            img_hash = hashlib.md5(img_b64[:200].encode()).hexdigest()
            seed = int(img_hash[:8], 16)
            rng = random.Random(seed)

            quality_score = round(rng.uniform(0.55, 0.95), 2)
            quality_scores.append(quality_score)

            # Simulate analysis results
            issues = []
            if quality_score < 0.7:
                issues.append("Image resolution is slightly blurry")
            if quality_score < 0.6:
                issues.append("Lighting and contrast hide product details")

            # Check listing match via description keywords
            listing_match = quality_score > 0.65
            if product_description or product_name:
                desc_lower = (product_description + " " + product_name).lower()
                # Simulate mismatch detection based on product name/description keywords
                if "premium" in desc_lower or "pro" in desc_lower or "high-end" in desc_lower:
                    if quality_score < 0.75:
                        listing_match = False
                        issues.append("Image indicates lower build quality than 'premium' claims")
                
                if "large" in desc_lower or "xl" in desc_lower:
                    listing_match = False
                    issues.append("Scale in image suggests product may be smaller than described")

            if not issues:
                issues.append(f"Image accurately represents the {product_name or 'product'}")

            image_results.append(
                {
                    "image_id": f"Image {idx}",
                    "quality_score": quality_score,
                    "listing_match": listing_match,
                    "match_label": f"Matches {product_name} listing"
                    if listing_match
                    else "Potential listing mismatch",
                    "issues": issues,
                }
            )

        # Aggregate scores
        avg_quality = (
            round(sum(quality_scores) / len(quality_scores), 2)
            if quality_scores
            else 0.75
        )
        overall_match = (
            all(r["listing_match"] for r in image_results) if image_results else True
        )

        result = {
            "image_quality_score": avg_quality,
            "image_listing_match": overall_match,
            "image_listing_match_score": avg_quality if overall_match else avg_quality * 0.6,
            "image_results": image_results,
        }

        logger.info(
            f"[ImageAnalysisAgent] quality={avg_quality}, match={overall_match}, "
            f"images_analyzed={len(image_results)}"
        )
        return result

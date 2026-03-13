"""
Agent 5 — Return Prediction Agent
Combines all agent signals into a prediction.
Uses weighted scoring to generate return_probability and risk_level.
"""
import logging

logger = logging.getLogger("ecommerce_agent.agents.return_prediction")

# Feature weights for prediction scoring
WEIGHTS = {
    "rating": -0.15,              # Higher rating = lower risk
    "negative_ratio": 0.30,       # Higher negative ratio = higher risk
    "cluster_density": 0.10,      # More complaint clusters = higher risk
    "image_quality_score": -0.10, # Better images = lower risk
    "listing_mismatch_score": 0.20,  # More mismatch = higher risk
    "external_complaints_score": 0.15,  # More external complaints = higher risk
    "review_count_factor": 0.10,  # Low review count = uncertain = moderate risk
}


class ReturnPredictionAgent:
    def run(
        self,
        rating: float,
        review_count: int,
        negative_ratio: float,
        clusters: list,
        image_quality_score: float,
        image_listing_match: bool,
        external_complaints_score: float,
        listing_mismatches: list,
        sentiment_distribution: dict,
    ) -> dict:
        """
        Combine all agent signals to predict return risk.
        Returns: {
            return_probability, risk_level,
            prediction_drivers[], feature_scores
        }
        """
        logger.info("[ReturnPredictionAgent] Computing prediction...")

        # Handle potential None inputs from standalone or incomplete prediction jobs
        rating = float(rating) if rating is not None else 3.5
        review_count = int(review_count) if review_count is not None else 0
        negative_ratio = float(negative_ratio) if negative_ratio is not None else 0.5
        clusters = clusters if clusters is not None else []
        image_quality_score = float(image_quality_score) if image_quality_score is not None else 0.5
        image_listing_match = bool(image_listing_match) if image_listing_match is not None else False
        external_complaints_score = float(external_complaints_score) if external_complaints_score is not None else 0.5
        listing_mismatches = listing_mismatches if listing_mismatches is not None else []
        sentiment_distribution = sentiment_distribution if sentiment_distribution is not None else {}

        # Normalize features to 0-1 scale safely
        rating_norm = max(0.0, min(1.0, (5.0 - rating) / 4.0))  # 5 → 0, 1 → 1
        neg_ratio = max(0.0, min(1.0, negative_ratio))
        cluster_density = max(0.0, min(1.0, len(clusters) / 5.0))
        img_quality = max(0.0, min(1.0, 1.0 - image_quality_score))  # Invert: low quality → high risk
        listing_mismatch_score = max(0.0, min(1.0, len(listing_mismatches) / 3.0))
        ext_score = max(0.0, min(1.0, external_complaints_score))
        review_factor = max(0.0, min(1.0, 1.0 - min(review_count, 50) / 50.0))  # Few reviews → higher uncertainty

        # Compute weighted sum
        raw_score = (
            WEIGHTS["rating"] * rating_norm
            + WEIGHTS["negative_ratio"] * neg_ratio
            + WEIGHTS["cluster_density"] * cluster_density
            + WEIGHTS["image_quality_score"] * img_quality
            + WEIGHTS["listing_mismatch_score"] * listing_mismatch_score
            + WEIGHTS["external_complaints_score"] * ext_score
            + WEIGHTS["review_count_factor"] * review_factor
        )

        # Shift and scale to 0-1 probability
        # Base probability around 0.4, then add/subtract based on signals
        return_probability = max(0.05, min(0.99, 0.4 + raw_score))
        
        # Failsafe cap in case of weird math
        if return_probability != return_probability: # NaN check
            return_probability = 0.50
            
        return_probability = round(return_probability, 2)

        # Risk level thresholds
        if return_probability < 0.3:
            risk_level = "LOW"
        elif return_probability <= 0.6:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"

        # Determine prediction drivers
        prediction_drivers = []

        neg_pct = sentiment_distribution.get("negative", 0)
        if neg_ratio > 0.3:
            prediction_drivers.append({
                "factor": "Negative review ratio",
                "impact": "high",
                "detail": f"{neg_pct}% of reviews are negative",
                "icon": "alert-triangle",
            })

        if listing_mismatch_score > 0.3:
            prediction_drivers.append({
                "factor": "Listing mismatch",
                "impact": "high",
                "detail": f"{len(listing_mismatches)} mismatches detected between listing and reviews",
                "icon": "git-compare",
            })

        if img_quality > 0.3:
            prediction_drivers.append({
                "factor": "Image quality mismatch",
                "impact": "medium",
                "detail": f"Image quality score: {image_quality_score}",
                "icon": "image",
            })

        if cluster_density > 0.4:
            prediction_drivers.append({
                "factor": "Complaint clusters",
                "impact": "medium",
                "detail": f"{len(clusters)} distinct complaint themes identified",
                "icon": "layers",
            })

        if rating < 3.5:
            prediction_drivers.append({
                "factor": "Product rating",
                "impact": "high",
                "detail": f"Rating is {rating}/5 — below acceptable threshold",
                "icon": "star",
            })
        elif rating < 4.0:
            prediction_drivers.append({
                "factor": "Product rating",
                "impact": "medium",
                "detail": f"Rating is {rating}/5 — moderate risk indicator",
                "icon": "star",
            })

        if ext_score > 0.5:
            prediction_drivers.append({
                "factor": "External complaints",
                "impact": "high",
                "detail": "Significant complaints found across web sources",
                "icon": "globe",
            })

        # If no strong drivers, add a baseline
        if not prediction_drivers:
            prediction_drivers.append({
                "factor": "Overall assessment",
                "impact": "low",
                "detail": "No significant risk factors detected",
                "icon": "check-circle",
            })

        # Feature scores for transparency
        feature_scores = {
            "rating_risk": round(rating_norm, 3),
            "negative_ratio": round(neg_ratio, 3),
            "cluster_density": round(cluster_density, 3),
            "image_quality_risk": round(img_quality, 3),
            "listing_mismatch": round(listing_mismatch_score, 3),
            "external_complaints": round(ext_score, 3),
            "review_uncertainty": round(review_factor, 3),
        }

        result = {
            "return_probability": return_probability,
            "risk_level": risk_level,
            "risk_score": int(return_probability * 100),
            "prediction_drivers": prediction_drivers,
            "feature_scores": feature_scores,
        }

        logger.info(
            f"[ReturnPredictionAgent] probability={return_probability}, "
            f"risk={risk_level}, drivers={len(prediction_drivers)}"
        )
        return result

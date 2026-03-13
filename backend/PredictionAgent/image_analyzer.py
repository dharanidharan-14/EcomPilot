import random
from typing import Dict, List, Optional

class ImageAnalyzer:
    def __init__(self):
        pass

    def analyze(self, image1_b64: Optional[str] = None, image2_b64: Optional[str] = None) -> Dict:
        """
        Simulates image analysis to detect product category, color, object clarity, and image quality.
        """
        images = []
        if image1_b64:
            images.append("image_1")
        if image2_b64:
            images.append("image_2")
            
        if not images:
            return {
                "categories": [],
                "color_detected": "Unknown",
                "object_clarity_score": 0,
                "image_quality_score": 0,
                "listing_match": False,
                "match_label": "No images attached",
                "issues": ["No product image provided"],
                "image_results": []
            }

        # Simulated dynamic analysis based on presence of images
        base_quality = random.uniform(0.65, 0.95)
        
        issues = []
        if base_quality < 0.75:
            issues.append("Slightly blurred or low resolution")
        if random.random() < 0.3:
            issues.append("Poor lighting detected")
            
        image_results = []
        for img in images:
            img_quality = min(1.0, base_quality + random.uniform(-0.1, 0.1))
            img_issues = list(issues)
            if random.random() < 0.2:
                img_issues.append("Background clutter")
                
            image_results.append({
                "image_id": img,
                "quality_score": round(img_quality, 2),
                "listing_match": img_quality > 0.7,
                "match_label": "Clear Listing Match" if img_quality > 0.7 else "Potential Image Issues",
                "issues": img_issues if img_issues else ["Image looks clear"]
            })

        avg_quality = sum((res["quality_score"] for res in image_results), 0) / len(image_results)

        return {
            "categories": ["Electronics", "Apparel", "Home", "Beauty"], # Simulated potential categories
            "color_detected": random.choice(["Black", "White", "Silver", "Multicolor"]),
            "object_clarity_score": round(avg_quality * 100, 0),
            "image_quality_score": round(avg_quality * 100, 0),
            "listing_match": avg_quality > 0.7,
            "match_label": "Clear Listing Match" if avg_quality > 0.7 else "Image Quality Concerns",
            "issues": issues,
            "image_results": image_results
        }

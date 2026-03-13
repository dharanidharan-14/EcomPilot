from typing import Dict

class FeatureFusion:
    def __init__(self):
        pass

    def fuse(self, image_data: Dict, text_data: Dict) -> Dict:
        """
        Combines image features and text features into a single structured dataset.
        """
        # Calculate combined quality and clarity metrics
        image_quality = image_data.get("image_quality_score", 0)
        listing_clarity = text_data.get("listing_clarity_score", 0)
        
        # Identify conflicts between image and text
        mismatches = []
        # Simulate logic: If we have an identified category from both, check if they align
        if image_data.get("categories") and text_data.get("category"):
            if text_data["category"] not in image_data["categories"]:
                mismatches.append(f"Text category ({text_data['category']}) may not strictly align with image categories ({', '.join(image_data['categories'][:2])})")
        
        missing_info = text_data.get("missing_info", [])
        if not image_data.get("image_results"):
            missing_info.append("No images provided for visual verification")
            
        return {
            "image_quality_score": image_quality,
            "listing_clarity_score": listing_clarity,
            "overall_quality_score": round((image_quality * 0.6) + (listing_clarity * 0.4), 0),
            "brand": text_data.get("brand", "Unknown"),
            "category": text_data.get("category", "Unknown"),
            "detected_color": image_data.get("color_detected", "Unknown"),
            "key_features": text_data.get("key_features", []),
            "missing_info": missing_info,
            "mismatches": mismatches,
            "image_issues": image_data.get("issues", [])
        }

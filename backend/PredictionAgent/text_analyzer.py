import random
import re
from typing import Dict

class TextAnalyzer:
    def __init__(self):
        pass

    def analyze(self, title: str, description: str) -> Dict:
        """
        Simulates NLP analysis of listing title and description.
        Extracts brand, product category, key features, and missing product info.
        """
        title = title or ""
        description = description or ""
        
        # Simple heuristics for simulation
        length_title = len(title)
        length_desc = len(description)
        
        # Mocks
        brands = ["Generic", "PremiumBrand", "EcoLife", "TechPro"]
        categories = ["Electronics", "Apparel", "Kitchen", "Toys"]
        
        detected_brand = random.choice(brands)
        detected_category = random.choice(categories)
        
        key_features = []
        words = description.split()
        if length_desc > 50:
            key_features.append("Detailed description provided")
        else:
            key_features.append("Brief description")
            
        if "warranty" in description.lower():
            key_features.append("Warranty mentioned")
        if "premium" in description.lower() or "high quality" in description.lower():
            key_features.append("Premium positioning")

        missing_info = []
        if length_title < 30:
            missing_info.append("Title lacks specific details")
        if length_desc < 100:
            missing_info.append("Description is too short, missing technical specs")
        if not re.search(r'\d+', description):
            missing_info.append("No numerical specifications (dimensions, weight, etc.)")
        if "color" not in description.lower():
            missing_info.append("Color not explicitly mentioned in description")

        clarity_score = min(100, (length_title * 0.5) + (length_desc * 0.1))
        
        return {
            "brand": detected_brand,
            "category": detected_category,
            "key_features": key_features,
            "missing_info": missing_info,
            "title_length": length_title,
            "description_length": length_desc,
            "listing_clarity_score": round(max(30, min(100, clarity_score)), 0)
        }

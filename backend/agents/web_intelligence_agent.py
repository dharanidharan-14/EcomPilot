"""
Agent 4 — Web Intelligence Agent
Searches the web for product complaints from external sources
(Reddit, Forums, Blogs, YouTube comments).
Uses intelligent mock data based on product name keywords.
"""
import logging
import hashlib
import random

logger = logging.getLogger("ecommerce_agent.agents.web_intelligence")

# Complaint templates by product category keywords
COMPLAINT_TEMPLATES = {
    "phone": [
        {"source": "Reddit r/smartphones", "complaint": "Battery drain after update", "severity": 0.7},
        {"source": "YouTube Comments", "complaint": "Screen flickering issue", "severity": 0.6},
        {"source": "Tech Forum", "complaint": "Mic quality drops during calls", "severity": 0.5},
        {"source": "Consumer Blog", "complaint": "Overheating during charging", "severity": 0.8},
    ],
    "headphone": [
        {"source": "Reddit r/headphones", "complaint": "ANC stops working randomly", "severity": 0.7},
        {"source": "YouTube Comments", "complaint": "Left earbud dies early", "severity": 0.8},
        {"source": "Audio Forum", "complaint": "Bluetooth connectivity drops", "severity": 0.6},
        {"source": "Consumer Blog", "complaint": "Ear pads peel after 3 months", "severity": 0.5},
    ],
    "laptop": [
        {"source": "Reddit r/laptops", "complaint": "Fan noise unbearable", "severity": 0.6},
        {"source": "YouTube Comments", "complaint": "Keyboard flex is concerning", "severity": 0.5},
        {"source": "Tech Forum", "complaint": "Battery life well below advertised", "severity": 0.7},
        {"source": "Consumer Blog", "complaint": "Trackpad stops responding", "severity": 0.8},
    ],
    "default": [
        {"source": "Reddit", "complaint": "Product quality lower than expected", "severity": 0.5},
        {"source": "YouTube Comments", "complaint": "Packaging was damaged", "severity": 0.3},
        {"source": "Consumer Forum", "complaint": "Customer service unresponsive", "severity": 0.6},
        {"source": "Review Blog", "complaint": "Not as described in listing", "severity": 0.7},
    ],
}


class WebIntelligenceAgent:
    def run(self, product_name: str, reviews: list = None) -> dict:
        """
        Search web for external product complaints.
        Returns: {
            external_complaints[], external_sentiment,
            external_complaints_score, complaint_sources[]
        }
        """
        logger.info(f"[WebIntelligenceAgent] Searching complaints for: {product_name}")

        # Determine category from product name
        name_lower = product_name.lower()
        category = "default"
        for cat in ["phone", "headphone", "laptop", "earphone", "earbuds", "tablet", "watch", "shirt", "shoe", "bottle"]:
            if cat in name_lower:
                category = cat if cat in COMPLAINT_TEMPLATES else "default"
                break
        if "ear" in name_lower:
            category = "headphone"

        templates = COMPLAINT_TEMPLATES.get(category, COMPLAINT_TEMPLATES["default"])
        
        # Build dynamic context if we have a descriptive title
        dynamic_complaints = []
        if len(product_name.split()) > 2 and category == "default":
            dynamic_complaints = [
                {"source": "Reddit Review", "complaint": f"The {product_name} didn't match the listing pictures at all.", "severity": 0.75},
                {"source": "Forum Comments", "complaint": f"A bit let down by the quality of the {product_name.split()[0]} item.", "severity": 0.65},
                {"source": "Consumer Blog", "complaint": "Found it was missing parts when it arrived.", "severity": 0.60},
                {"source": "YouTube", "complaint": "Not the best value for money", "severity": 0.50}
            ]
            templates = dynamic_complaints

        # Deterministic selection based on product name hash
        name_hash = hashlib.md5(product_name.encode()).hexdigest()
        seed = int(name_hash[:8], 16)
        rng = random.Random(seed)

        # Select 2-4 complaints
        num_complaints = rng.randint(2, min(4, len(templates)))
        selected = rng.sample(templates, num_complaints)

        # Calculate external sentiment
        avg_severity = sum(c["severity"] for c in selected) / len(selected)
        external_sentiment = "negative" if avg_severity > 0.6 else "mixed"

        complaint_sources = []
        for c in selected:
            complaint_sources.append({
                "source": c["source"],
                "complaint": c["complaint"],
                "severity": c["severity"],
            })

        result = {
            "external_complaints": [c["complaint"] for c in selected],
            "external_sentiment": external_sentiment,
            "external_complaints_score": round(avg_severity, 2),
            "complaint_sources": complaint_sources,
        }

        logger.info(
            f"[WebIntelligenceAgent] Found {len(selected)} external complaints, "
            f"sentiment={external_sentiment}"
        )
        return result

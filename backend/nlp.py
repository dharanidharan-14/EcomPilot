import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer
import re

class NLPPipeline:
    def __init__(self):
        # We'll use a lightweight model for embeddings
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def clean_text(self, text: str):
        # Basic cleaning
        text = text.lower()
        text = re.sub(r'[^\w\s]', '', text)
        return text.strip()

    def process_reviews(self, reviews: list):
        if not reviews:
            return []

        cleaned_reviews = [self.clean_text(r) for r in reviews]
        embeddings = self.model.encode(cleaned_reviews)

        # Determine number of clusters dynamically based on review count
        if len(reviews) <= 3:
            num_clusters = len(reviews)
        elif len(reviews) <= 10:
            num_clusters = 3
        else:
            num_clusters = 5

        if num_clusters < 2:
            return [{"theme": "General Feedback", "percentage": 100.0, "example_reviews": reviews}]

        kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
        kmeans.fit(embeddings)
        
        clusters = []
        for i in range(num_clusters):
            indices = np.where(kmeans.labels_ == i)[0]
            if len(indices) == 0: continue # Skip empty clusters
            
            cluster_reviews = [reviews[idx] for idx in indices]
            percentage = (len(cluster_reviews) / len(reviews)) * 100
            
            # Expanded heuristic for theme labeling
            all_text = " ".join(cluster_reviews).lower()
            
            theme_map = {
                "Sizing & Fit Issues": ["size", "fit", "small", "large", "tight", "loose", "short", "long", "inch", "cm", "measure"],
                "Material & Quality Defects": ["break", "broke", "cheap", "quality", "material", "torn", "plastic", "fake", "sturdy", "durability"],
                "Packaging & Delivery Damage": ["box", "package", "damage", "deliver", "dent", "crush", "wrap", "open", "ship"],
                "Product Mismatch from Description": ["color", "picture", "look", "expect", "different", "mislead", "photo", "image", "wrong", "mismatch"],
                "Functional Defects": ["work", "stop", "defective", "fail", "broken", "battery", "charge", "button", "screen", "power", "functional"],
                "Comfort & Ergonomics": ["hurt", "pain", "hard", "soft", "heavy", "light", "wear", "feel", "strap"]
            }
            
            candidate_themes = {}
            for theme, keywords in theme_map.items():
                count = sum(1 for kw in keywords if kw in all_text)
                if count > 0:
                    candidate_themes[theme] = count
            
            if candidate_themes:
                theme_name = max(candidate_themes, key=candidate_themes.get)
            else:
                fallback_names = list(theme_map.keys())
                theme_name = fallback_names[i % len(fallback_names)]
            
            clusters.append({
                "theme": theme_name,
                "percentage": round(percentage, 2),
                "example_reviews": cluster_reviews[:3]
            })
            
        # Sort by percentage descending
        clusters.sort(key=lambda x: x["percentage"], reverse=True)
        return clusters

    def calculate_risk_score(self, negative_ratio, severity, mismatch_count):
        # Improved Risk Formula:
        # Higher weights on mismatch and severity, base logic is more stable
        # weights: net_ratio: 0.3, severity: 0.35, mismatch: 0.25, base: 0.1
        
        score = (negative_ratio * 30) + (severity * 35) + (min(mismatch_count, 5) * 5) + 10
        # Boost score slightly if negative ratio is high (> 40%)
        if negative_ratio > 0.4:
            score += 10
            
        return min(max(int(score), 0), 100)

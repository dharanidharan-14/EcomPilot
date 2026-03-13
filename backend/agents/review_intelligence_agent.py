"""
Agent 2 — Review Intelligence Agent
Processes reviews for sentiment analysis, complaint extraction,
cluster generation, and negativity ratio calculation.
"""
import logging
import re
from nlp import NLPPipeline

logger = logging.getLogger("ecommerce_agent.agents.review_intelligence")

# Sentiment keyword lists
NEGATIVE_KEYWORDS = [
    "bad", "worst", "terrible", "horrible", "poor", "defective", "broken",
    "waste", "useless", "disappointed", "disappointing", "fail", "failed",
    "return", "refund", "cheap", "fake", "scam", "fraud", "not working",
    "stopped", "damaged", "issue", "problem", "complaint", "regret",
    "awful", "pathetic", "rubbish", "trash", "malfunction", "overheating",
    "slow", "lag", "battery drain", "crack", "scratch", "flimsy",
]

POSITIVE_KEYWORDS = [
    "good", "great", "excellent", "amazing", "love", "perfect", "best",
    "awesome", "fantastic", "wonderful", "satisfied", "happy", "recommend",
    "premium", "quality", "worth", "solid", "durable", "fast", "smooth",
    "beautiful", "comfortable", "reliable", "superb", "outstanding",
]


class ReviewIntelligenceAgent:
    def __init__(self, nlp_pipeline: NLPPipeline):
        self.nlp = nlp_pipeline

    def run(self, reviews: list) -> dict:
        """
        Process reviews and return intelligence data.
        Returns: {
            negative_ratio, clusters[], sentiment_distribution
        }
        """
        logger.info(f"[ReviewIntelligenceAgent] Processing {len(reviews)} reviews")

        if not reviews:
            return {
                "negative_ratio": 0.0,
                "clusters": [],
                "sentiment_distribution": {
                    "positive": 0, "negative": 0, "neutral": 0
                },
            }

        # Sentiment analysis
        positive = 0
        negative = 0
        neutral = 0

        for review in reviews:
            review_lower = review.lower()
            neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in review_lower)
            pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in review_lower)

            if neg_count > pos_count:
                negative += 1
            elif pos_count > neg_count:
                positive += 1
            else:
                neutral += 1

        total = len(reviews)
        negative_ratio = round(negative / total, 3) if total > 0 else 0.0

        # Complaint clustering via existing NLP pipeline
        clusters = self.nlp.process_reviews(reviews)

        sentiment_distribution = {
            "positive": round(positive / total * 100, 1) if total else 0,
            "negative": round(negative / total * 100, 1) if total else 0,
            "neutral": round(neutral / total * 100, 1) if total else 0,
        }

        logger.info(
            f"[ReviewIntelligenceAgent] neg_ratio={negative_ratio}, "
            f"clusters={len(clusters)}, sentiment={sentiment_distribution}"
        )

        return {
            "negative_ratio": negative_ratio,
            "clusters": clusters,
            "sentiment_distribution": sentiment_distribution,
        }

from pydantic import BaseModel, HttpUrl
from typing import List, Optional, Dict
from datetime import datetime


class AnalysisRequest(BaseModel):
    url: HttpUrl


class PredictionRequest(BaseModel):
    url: str
    image1_b64: Optional[str] = None
    image2_b64: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None


class StandalonePredictionRequest(BaseModel):
    title: str
    description: str
    image1_b64: Optional[str] = None
    image2_b64: Optional[str] = None


class PredictionRunRequest(BaseModel):
    product_images: List[str] = []
    product_title: str
    product_description: str


class ComplaintCluster(BaseModel):
    theme: str
    percentage: float
    example_reviews: List[str]


class ListingMismatch(BaseModel):
    listing_claim: str
    review_evidence: str


class PredictionDriver(BaseModel):
    factor: str
    impact: str  # low, medium, high
    detail: str
    icon: str


class ImageAnalysisResult(BaseModel):
    image_id: str
    quality_score: float
    listing_match: bool
    match_label: str
    issues: List[str]


class ComplaintSource(BaseModel):
    source: str
    complaint: str
    severity: float


class Suggestions(BaseModel):
    listing_improvements: List[str]
    customer_expectation_fixes: List[str]
    seller_optimization: List[str]


class ReturnCostBreakdown(BaseModel):
    logistics: int
    refunds: int
    warehouse: int
    restocking: int


class PotentialSavings(BaseModel):
    better_images: int
    clear_description: int
    size_chart: int
    better_packaging: int


class CostEstimation(BaseModel):
    return_cost_breakdown: ReturnCostBreakdown
    potential_savings: PotentialSavings


class PredictionReport(BaseModel):
    return_probability: float
    risk_level: str  # LOW, MEDIUM, HIGH
    risk_score: int  # 0-100
    prediction_drivers: List[PredictionDriver]
    feature_scores: Dict[str, float]
    image_analysis: List[ImageAnalysisResult]
    complaint_clusters: List[ComplaintCluster]
    external_complaints: List[str]
    complaint_sources: List[ComplaintSource]
    sentiment_distribution: Dict[str, float]


class AnalysisReport(BaseModel):
    product_name: str
    platform: str
    rating: float
    total_reviews: int
    complaint_clusters: List[ComplaintCluster]
    listing_mismatches: List[ListingMismatch]
    return_risk_score: int  # 0-100
    risk_level: str  # Low, Medium, High
    top_return_reasons: List[str]
    low_sales_reasons: List[str]
    recommendations: List[str]
    prediction: Optional[PredictionReport] = None
    suggestions: Optional[Suggestions] = None
    cost_estimation: Optional[CostEstimation] = None
    timestamp: datetime = datetime.now()


class JobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[AnalysisReport] = None


class StandaloneJobStatus(BaseModel):
    job_id: str
    status: str  # pending, running, completed, failed
    progress: int  # 0-100
    message: str
    result: Optional[PredictionReport] = None

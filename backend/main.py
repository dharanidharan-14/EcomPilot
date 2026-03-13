from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
import logging
import json
import sys
import asyncio
from typing import Dict

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from schemas import (
    AnalysisRequest, JobStatus, AnalysisReport,
    PredictionRequest, PredictionReport, PredictionDriver,
    ImageAnalysisResult, ComplaintSource, ComplaintCluster,
    StandalonePredictionRequest, StandaloneJobStatus
)
from database import SessionLocal, DBReport

# Configure structured logging
logging.basicConfig(
    level=logging.INFO,
    format='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger("ecommerce_agent")

app = FastAPI(title="EcomPilot AI – Product Return Intelligence API")

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from scraper import UniversalScraper
from nlp import NLPPipeline
from agent import AIIntelligenceAgent

# Import agents
from agents.scraping_agent import ScrapingAgent
from agents.review_intelligence_agent import ReviewIntelligenceAgent
from agents.image_analysis_agent import ImageAnalysisAgent
from agents.web_intelligence_agent import WebIntelligenceAgent
from agents.return_prediction_agent import ReturnPredictionAgent
from agents.suggestion_agent import SuggestionAgent

# In-memory job storage
jobs: Dict[str, JobStatus] = {}
standalone_jobs: Dict[str, StandaloneJobStatus] = {}

# Initialize core modules
scraper = UniversalScraper()
nlp = NLPPipeline()
agent = AIIntelligenceAgent()

# Initialize agents
scraping_agent = ScrapingAgent(scraper)
review_agent = ReviewIntelligenceAgent(nlp)
image_agent = ImageAnalysisAgent()
web_agent = WebIntelligenceAgent()
prediction_agent = ReturnPredictionAgent()
suggestion_agent = SuggestionAgent()


@app.on_event("startup")
async def startup_event():
    await scraper.start()


@app.on_event("shutdown")
async def shutdown_event():
    await scraper.stop()


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/api/analyze", response_model=Dict[str, str])
async def submit_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    logger.info(f"Received analysis request for URL: {request.url}. Job ID: {job_id}")
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Job submitted and queued",
        result=None
    )
    
    background_tasks.add_task(run_analysis_job, job_id, str(request.url))
    return {"job_id": job_id}


@app.post("/api/predict-return")
async def submit_prediction(request: PredictionRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    logger.info(f"Received prediction request for URL: {request.url}. Job ID: {job_id}")
    jobs[job_id] = JobStatus(
        job_id=job_id,
        status="pending",
        progress=0,
        message="Prediction job submitted and queued",
        result=None
    )
    
    background_tasks.add_task(
        run_prediction_job, job_id, request.url,
        request.image1_b64, request.image2_b64,
        request.title, request.description
    )
    return {"job_id": job_id}


@app.post("/api/predict-standalone", response_model=Dict[str, str])
async def submit_standalone_prediction(request: StandalonePredictionRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    logger.info(f"Received standalone prediction request. Job ID: {job_id}")
    standalone_jobs[job_id] = StandaloneJobStatus(
        job_id=job_id,
        status="completed", # Simulation finishes quickly, so we handle it synchronously for simplicity
        progress=100,
        message="Prediction complete",
        result=None
    )
    
    # Run the "agentic simulation" for standalone prediction
    report = await asyncio.to_thread(
        run_standalone_prediction_job,
        request.title, request.description,
        request.image1_b64, request.image2_b64
    )
    
    standalone_jobs[job_id].result = report
    return {"job_id": job_id}

from schemas import PredictionRunRequest
from PredictionAgent.prediction_controller import PredictionController

@app.post("/api/prediction/run")
async def run_prediction_agent(request: PredictionRunRequest):
    controller = PredictionController()
    try:
        result = await asyncio.to_thread(
            controller.run_pipeline,
            request.product_images,
            request.product_title,
            request.product_description
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Prediction run failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/status/{job_id}", response_model=JobStatus)
async def get_status(job_id: str):
    if job_id in jobs:
        return jobs[job_id]
    if job_id in standalone_jobs:
        # Cast to match or handle differently, frontend just needs progress/status/message/result loosely
        sj = standalone_jobs[job_id]
        return JobStatus(job_id=sj.job_id, status=sj.status, progress=sj.progress, message=sj.message)
    raise HTTPException(status_code=404, detail="Job not found")


@app.get("/api/report/{job_id}", response_model=AnalysisReport)
async def get_report(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    if jobs[job_id].status != "completed":
        raise HTTPException(status_code=400, detail="Job not yet completed")
    return jobs[job_id].result


def run_standalone_prediction_job(title: str, description: str, image1_b64: str, image2_b64: str) -> PredictionReport:
    """Standalone prediction pipeline (no scraping)."""
    # 1. Image Analysis
    image_data = image_agent.run(
        image1_b64=image1_b64, 
        image2_b64=image2_b64, 
        product_description=description, 
        product_name=title
    )
    
    # 2. Review Intelligence (Mock data without URL)
    clusters = [
        {"theme": "General quality", "percentage": 45, "example_reviews": ["Feels cheap", "Not as described"]},
        {"theme": "Sizing issues", "percentage": 35, "example_reviews": ["Way too small", "Size chart is wrong"]}
    ]
    sentiment_dist = {"positive": 30, "neutral": 20, "negative": 50}
    
    # 3. Web Intelligence (Mock search based on title)
    web_data = web_agent.run(title, [])
    
    # 4. Return Prediction Agent (XGBoost simulation)
    # Give a default rating/review count for standalone prediction
    prediction_data = prediction_agent.run(
        rating=3.5,
        review_count=150,
        negative_ratio=0.5,
        clusters=clusters,
        image_quality_score=image_data["image_quality_score"],
        image_listing_match=image_data["image_listing_match"],
        external_complaints_score=web_data["external_complaints_score"],
        listing_mismatches=[{"listing_claim": "High quality", "review_evidence": "Broke in 2 days"}],
        sentiment_distribution=sentiment_dist
    )
    
    # Build report
    return PredictionReport(
        return_probability=prediction_data["return_probability"],
        risk_level=prediction_data["risk_level"],
        risk_score=prediction_data["risk_score"],
        prediction_drivers=[PredictionDriver(**d) for d in prediction_data["prediction_drivers"]],
        feature_scores=prediction_data["feature_scores"],
        image_analysis=[ImageAnalysisResult(**r) for r in image_data["image_results"]],
        complaint_clusters=[ComplaintCluster(**c) for c in clusters],
        external_complaints=web_data["external_complaints"],
        complaint_sources=[ComplaintSource(**s) for s in web_data["complaint_sources"]],
        sentiment_distribution=sentiment_dist,
    )


async def run_prediction_job(
    job_id: str, url: str,
    image1_b64: str = None, image2_b64: str = None,
    title: str = None, description: str = None
):
    """Full agentic prediction pipeline with 6 steps."""
    try:
        logger.info(f"Starting prediction job {job_id} for {url}")

        # ── Step 1: Scraping Agent ──
        jobs[job_id].status = "running"
        jobs[job_id].progress = 8
        jobs[job_id].message = "Agent 1: Scraping product data..."
        scrape_data = await scraping_agent.run(url)

        if "error" in scrape_data:
            logger.error(f"Job {job_id} scraping failed: {scrape_data['error']}")
            jobs[job_id].status = "failed"
            jobs[job_id].message = f"Scraping failed: {scrape_data['error']}"
            return

        product_name = title or scrape_data["product_name"]
        product_desc = description or scrape_data.get("description", "")
        rating = scrape_data.get("rating", 4.0)
        reviews = scrape_data.get("reviews", [])

        logger.info(f"Job {job_id}: Scraped {len(reviews)} reviews")

        # ── Step 2: Review Intelligence Agent ──
        jobs[job_id].progress = 25
        jobs[job_id].message = "Agent 2: Analyzing review intelligence..."
        review_data = await asyncio.to_thread(review_agent.run, reviews)

        # ── Step 3: AI Intelligence (Existing Agent) ──
        jobs[job_id].progress = 40
        jobs[job_id].message = "Agent 3: Running AI intelligence analysis..."
        clusters = review_data["clusters"]
        ai_analysis = await agent.analyze_with_llm(clusters, scrape_data)

        # ── Step 4: Image Analysis Agent ──
        jobs[job_id].progress = 55
        jobs[job_id].message = "Agent 4: Analyzing product images..."
        image_data = await asyncio.to_thread(
            image_agent.run,
            image1_b64=image1_b64,
            image2_b64=image2_b64,
            product_description=product_desc,
            product_name=product_name,
        )

        # ── Step 5: Web Intelligence Agent ──
        jobs[job_id].progress = 70
        jobs[job_id].message = "Agent 5: Scanning web for complaints..."
        web_data = await asyncio.to_thread(web_agent.run, product_name, reviews)

        # ── Step 6: Return Prediction Agent ──
        jobs[job_id].progress = 85
        jobs[job_id].message = "Agent 6: Computing return prediction..."
        prediction_data = await asyncio.to_thread(
            prediction_agent.run,
            rating=rating,
            review_count=len(reviews),
            negative_ratio=review_data["negative_ratio"],
            clusters=clusters,
            image_quality_score=image_data["image_quality_score"],
            image_listing_match=image_data["image_listing_match"],
            external_complaints_score=web_data["external_complaints_score"],
            listing_mismatches=ai_analysis.get("listing_mismatches", []),
            sentiment_distribution=review_data["sentiment_distribution"],
        )

        # ── Build prediction report ──
        prediction_report = PredictionReport(
            return_probability=prediction_data["return_probability"],
            risk_level=prediction_data["risk_level"],
            risk_score=prediction_data["risk_score"],
            prediction_drivers=[PredictionDriver(**d) for d in prediction_data["prediction_drivers"]],
            feature_scores=prediction_data["feature_scores"],
            image_analysis=[ImageAnalysisResult(**r) for r in image_data["image_results"]],
            complaint_clusters=[
                ComplaintCluster(**c) if isinstance(c, dict) else c
                for c in clusters
            ],
            external_complaints=web_data["external_complaints"],
            complaint_sources=[ComplaintSource(**s) for s in web_data["complaint_sources"]],
            sentiment_distribution=review_data["sentiment_distribution"],
        )

        # ── Build risk score from prediction ──
        risk_score = prediction_data["risk_score"]
        risk_level_display = prediction_data["risk_level"].capitalize()

        # ── Construct final report ──
        report = AnalysisReport(
            product_name=product_name,
            platform=scrape_data["platform"],
            rating=rating,
            total_reviews=len(reviews),
            complaint_clusters=[
                ComplaintCluster(**c) if isinstance(c, dict) else c
                for c in clusters
            ],
            listing_mismatches=[
                {"listing_claim": m["listing_claim"], "review_evidence": m["review_evidence"]}
                for m in ai_analysis.get("listing_mismatches", [])
            ],
            return_risk_score=risk_score,
            risk_level=risk_level_display,
            top_return_reasons=[c["theme"] if isinstance(c, dict) else c.theme for c in clusters[:3]],
            low_sales_reasons=["High return risk observed"] if risk_score > 50 else ["Moderate risk factors present"],
            recommendations=ai_analysis.get("recommendations", []),
            prediction=prediction_report,
        )

        jobs[job_id].result = report
        jobs[job_id].progress = 100
        jobs[job_id].status = "completed"
        jobs[job_id].message = "Prediction analysis complete"
        logger.info(f"Job {job_id} completed — risk={prediction_data['risk_level']}, prob={prediction_data['return_probability']}")

        # Save to DB
        db = SessionLocal()
        try:
            db_report = DBReport(
                id=job_id,
                product_name=report.product_name,
                platform=report.platform,
                rating=report.rating,
                total_reviews=report.total_reviews,
                complaint_clusters=[c.dict() if hasattr(c, "dict") else c for c in report.complaint_clusters],
                listing_mismatches=[m.dict() if hasattr(m, "dict") else m for m in report.listing_mismatches],
                return_risk_score=report.return_risk_score,
                risk_level=report.risk_level,
                top_return_reasons=report.top_return_reasons,
                recommendations=report.recommendations,
            )
            db.add(db_report)
            db.commit()
            logger.info(f"Job {job_id} saved to database")
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Job {job_id} failed with unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        jobs[job_id].status = "failed"
        jobs[job_id].message = f"Unexpected error: {str(e)}"


async def run_analysis_job(job_id: str, url: str):
    try:
        logger.info(f"Starting job {job_id} for {url}")
        
        # Step 1: Scraping
        jobs[job_id].status = "running"
        jobs[job_id].progress = 14
        jobs[job_id].message = "Scraping reviews..."
        scrape_data = await scraper.scrape_reviews(url)
        
        if "error" in scrape_data:
            logger.error(f"Job {job_id} scraping failed: {scrape_data['error']}")
            jobs[job_id].status = "failed"
            jobs[job_id].message = f"Scraping failed: {scrape_data['error']}"
            return

        logger.info(f"Job {job_id}: Scraped {len(scrape_data.get('reviews', []))} reviews")

        # Step 2: Cleaning (simulated)
        jobs[job_id].progress = 28
        jobs[job_id].message = "Cleaning and filtering data..."
        await asyncio.sleep(1) # Simulate cleaning time

        # Step 3: NLP Processing (Clustering)
        jobs[job_id].progress = 42
        jobs[job_id].message = "Clustering reviews..."
        clusters = await asyncio.to_thread(nlp.process_reviews, scrape_data["reviews"])
        
        # Step 4: AI Intelligence Analysis
        jobs[job_id].progress = 56
        jobs[job_id].message = "Analyzing with AI Agent..."
        ai_analysis = await agent.analyze_with_llm(clusters, scrape_data)
        
        # Step 5: Prediction Calculate Risk Score
        jobs[job_id].progress = 70
        jobs[job_id].message = "Predicting return risk..."
        
        # Calculate dynamic sentiment score based on scraped reviews
        reviews_list = scrape_data.get("reviews", [])
        neg_count = sum(1 for r in reviews_list if any(kw in r.lower() for kw in ["bad", "poor", "broken", "worst", "cheap", "defective", "disappointed", "low quality", "terrible", "waste"]))
        neg_ratio = neg_count / max(1, len(reviews_list))
        severity = min(0.9, neg_ratio * 1.5) 
        
        mismatch_count = len(ai_analysis.get("listing_mismatches", []))
        risk_score = nlp.calculate_risk_score(neg_ratio, severity, mismatch_count)
        
        # Consistent baseline for no reviews
        if not reviews_list:
            risk_score = 10 # Baseline score for unverified product
            
        risk_level = "Low"
        if risk_score > 60: risk_level = "High"
        elif risk_score > 30: risk_level = "Medium"

        # Step 6: Reporting (Finalizing report)
        jobs[job_id].progress = 85
        jobs[job_id].message = "Generating reports..."
        await asyncio.sleep(0.5)

        # Step 7: Suggestion Agent
        jobs[job_id].progress = 95
        jobs[job_id].message = "Generating AI Suggestions..."
        suggestion_data = await asyncio.to_thread(
            suggestion_agent.run,
            risk_score=risk_score,
            total_reviews=len(scrape_data["reviews"]),
            clusters=clusters,
            mismatches=ai_analysis.get("listing_mismatches", [])
        )

        from schemas import Suggestions, CostEstimation, ReturnCostBreakdown, PotentialSavings

        sug_model = Suggestions(**suggestion_data["suggestions"])
        cost_model = CostEstimation(
            return_cost_breakdown=ReturnCostBreakdown(**suggestion_data["cost_estimation"]["return_cost_breakdown"]),
            potential_savings=PotentialSavings(**suggestion_data["cost_estimation"]["potential_savings"])
        )

        # Construct final report
        report = AnalysisReport(
            product_name=scrape_data["product_name"],
            platform=scrape_data["platform"],
            rating=4.0, 
            total_reviews=len(scrape_data["reviews"]),
            complaint_clusters=clusters,
            listing_mismatches=ai_analysis.get("listing_mismatches", []),
            return_risk_score=risk_score,
            risk_level=risk_level,
            top_return_reasons=[c["theme"] for c in clusters[:2]],
            low_sales_reasons=["High return risk observed"],
            recommendations=ai_analysis.get("recommendations", []),
            suggestions=sug_model,
            cost_estimation=cost_model
        )
        
        jobs[job_id].result = report
        jobs[job_id].progress = 100
        jobs[job_id].status = "completed"
        jobs[job_id].message = "Analysis complete"
        logger.info(f"Job {job_id} completed successfully")

        # Save to DB
        db = SessionLocal()
        try:
            db_report = DBReport(
                id=job_id,
                product_name=report.product_name,
                platform=report.platform,
                rating=report.rating,
                total_reviews=report.total_reviews,
                complaint_clusters=[c.dict() if hasattr(c, "dict") else c for c in report.complaint_clusters],
                listing_mismatches=[m.dict() if hasattr(m, "dict") else m for m in report.listing_mismatches],
                return_risk_score=report.return_risk_score,
                risk_level=report.risk_level,
                top_return_reasons=report.top_return_reasons,
                recommendations=report.recommendations
            )
            db.add(db_report)
            db.commit()
            logger.info(f"Job {job_id} saved to database")
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Job {job_id} failed with unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        jobs[job_id].status = "failed"
        jobs[job_id].message = f"Unexpected error: {str(e)}"

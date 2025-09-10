"""
FastAPI endpoints for the AI Startup Copilot API.
"""

import logging
from datetime import datetime, timezone
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends
from celery.result import AsyncResult
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.api.v1.schemas import (
    AnalysisRequest,
    AnalysisTaskResponse,
    AnalysisStatusResponse,
    CompanyReportResponse,
    ErrorResponse
)
from app.workers.celery_app import celery_app
from app.workers.tasks import run_startup_analysis
from app.core.mongo_client import get_async_database

# Configure logging
logger = logging.getLogger(__name__)

# Create API router
router = APIRouter()


@router.post(
    "/analyze",
    response_model=AnalysisTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start startup analysis",
    description="Submit a startup for analysis. Returns a task ID to track progress or existing company ID if already analyzed.",
    responses={
        200: {"description": "Analysis already exists"},
        202: {"description": "Analysis task created successfully"},
        400: {"model": ErrorResponse, "description": "Invalid request data"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def analyze_startup(
    request: AnalysisRequest,
    db: AsyncIOMotorDatabase = Depends(get_async_database)
) -> AnalysisTaskResponse:
    """
    Start asynchronous analysis of a startup with caching.
    
    This endpoint first checks if the company has already been analyzed.
    If found, it returns the existing analysis. Otherwise, it queues a new
    analysis task for background processing using Celery.
    
    Args:
        request: Analysis request containing company name and URL
        db: MongoDB database dependency
        
    Returns:
        AnalysisTaskResponse with task ID for tracking or existing company info
    """
    try:
        logger.info(f"Received analysis request for {request.company_name}")
        
        # Convert HttpUrl to string for database queries (if provided)
        company_url_str = str(request.company_url) if request.company_url else None
        
        # Check if analysis already exists in MongoDB for this specific analysis type
        existing_analysis = None
        search_criteria = {
            "status": "completed"
        }
        
        if company_url_str:
            search_criteria["company_url"] = company_url_str
        else:
            search_criteria["company_name"] = request.company_name
        
        # Only return cached result for the same analysis type
        search_criteria["analysis_type"] = request.analysis_type
        
        logger.info(f"Checking for existing {request.analysis_type} analysis")
        existing_analysis = await db.startup_profiles.find_one(search_criteria)
        
        if existing_analysis:
            logger.info(f"Found existing analysis for {request.company_name}")
            
            # Return 200 OK with existing analysis info
            from fastapi import Response
            response = Response(status_code=status.HTTP_200_OK)
            
            return AnalysisTaskResponse(
                task_id=str(existing_analysis["_id"]),
                message=f"Analysis already complete for {request.company_name}. Use /report/{existing_analysis['_id']} to get the full report."
            )
        
        # Check if there's a pending analysis
        pending_analysis = await db.startup_profiles.find_one({
            "company_url": company_url_str,
            "status": {"$in": ["pending", "in_progress"]}
        })
        
        if pending_analysis:
            # Find the associated task ID
            task_id = pending_analysis.get("task_id")
            if task_id:
                logger.info(f"Found pending analysis for {request.company_name} (task: {task_id})")
                return AnalysisTaskResponse(
                    task_id=task_id,
                    message=f"Analysis already in progress for {request.company_name}"
                )
        
        # No existing analysis found, create new task
        logger.info(f"No existing analysis found, creating new task for {request.company_name}")
        
        # Queue the analysis task with all parameters
        task = run_startup_analysis.delay(
            company_name=request.company_name,
            company_url=company_url_str,
            additional_info=request.additional_info,
            analysis_type=request.analysis_type
        )
        
        # Create a pending record in MongoDB to track the task
        pending_record = {
            "company_name": request.company_name,
            "company_url": company_url_str,
            "status": "pending",
            "task_id": task.id,
            "created_at": datetime.now(timezone.utc)
        }
        
        try:
            await db.startup_profiles.insert_one(pending_record)
            logger.info(f"Created pending record for task {task.id}")
        except Exception as e:
            logger.warning(f"Failed to create pending record: {e}")
        
        logger.info(f"Queued analysis task {task.id} for {request.company_name}")
        
        return AnalysisTaskResponse(
            task_id=task.id,
            message="Analysis task created successfully"
        )
        
    except Exception as e:
        logger.error(f"Failed to create analysis task: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create analysis task: {str(e)}"
        )


@router.get(
    "/status/{task_id}",
    response_model=AnalysisStatusResponse,
    summary="Get analysis status",
    description="Check the status of an analysis task using its task ID.",
    responses={
        200: {"description": "Task status retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_analysis_status(task_id: str) -> AnalysisStatusResponse:
    """
    Get the status of an analysis task.
    
    Args:
        task_id: Unique identifier of the analysis task
        
    Returns:
        AnalysisStatusResponse with current task status and results
    """
    try:
        logger.info(f"Checking status for task {task_id}")
        
        # First check MongoDB directly for the task
        try:
            from app.core.mongo_client import get_async_database
            db = await get_async_database()
            mongo_doc = await db.startup_profiles.find_one({"task_id": task_id})
            
            if mongo_doc:
                logger.info(f"Found MongoDB document for task {task_id}: status={mongo_doc.get('status')}")
                # We found the task in MongoDB
                if mongo_doc.get("status") == "completed":
                    return AnalysisStatusResponse(
                        task_id=task_id,
                        status="SUCCESS",
                        result={
                            "company_name": mongo_doc.get("company_name"),
                            "company_url": mongo_doc.get("company_url"),
                            "status": "Analysis Complete",
                            "mongodb_id": str(mongo_doc.get("_id")),
                            "summary": mongo_doc.get("analysis", {}).get("summary", ""),
                            "processing_time_seconds": mongo_doc.get("processing_time_seconds", 0),
                            "analysis_date": mongo_doc.get("created_at").isoformat() if mongo_doc.get("created_at") else None
                        }
                    )
                elif mongo_doc.get("status") == "failed":
                    return AnalysisStatusResponse(
                        task_id=task_id,
                        status="FAILURE",
                        error=mongo_doc.get("error", "Task failed")
                    )
                else:
                    logger.info(f"MongoDB document status is: '{mongo_doc.get('status')}' (not 'completed')")
            else:
                logger.info(f"No MongoDB document found for task {task_id}")
        except Exception as e:
            logger.warning(f"Could not check MongoDB: {e}")
        
        # Get task result from Celery (only for state, not result)
        try:
            task_result = AsyncResult(task_id, app=celery_app)
            task_state = task_result.state
        except Exception as e:
            logger.error(f"Could not get Celery task state: {e}")
            task_state = "UNKNOWN"
        
        # Prepare response based on task state
        response = AnalysisStatusResponse(
            task_id=task_id,
            status=task_state
        )
        
        # Handle different task states
        if task_state == "PENDING":
            response.result = {"message": "Task is waiting to be processed"}
        elif task_state == "STARTED":
            response.result = {"message": "Task has started processing"}
        elif task_state in ["PROGRESS", "RETRY"]:
            response.result = {"message": "Task is in progress"}
            # Try to get progress info safely
            try:
                task_result = AsyncResult(task_id, app=celery_app)
                if hasattr(task_result, 'info') and task_result.info:
                    response.progress = task_result.info
            except:
                pass
        elif task_state == "SUCCESS":
            response.result = {"message": "Task completed - check MongoDB for results"}
        elif task_state == "FAILURE":
            response.error = "Task failed - check logs for details"
        else:
            response.result = {"message": f"Task is in {task_state} state"}
        
        logger.info(f"Task {task_id} status: {task_state}")
        return response
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to get task status for {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get task status: {str(e)}"
        )


@router.get(
    "/report/{company_id}",
    response_model=CompanyReportResponse,
    summary="Get company analysis report",
    description="Retrieve the full analysis report for a company from MongoDB.",
    responses={
        200: {"description": "Company report retrieved successfully"},
        404: {"model": ErrorResponse, "description": "Company not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_company_report(
    company_id: str,
    db: AsyncIOMotorDatabase = Depends(get_async_database)
) -> CompanyReportResponse:
    """
    Get the full analysis report for a company from MongoDB.
    
    Args:
        company_id: MongoDB ObjectId of the company document
        db: MongoDB database dependency
        
    Returns:
        CompanyReportResponse with full analysis report
    """
    try:
        logger.info(f"Retrieving report for company {company_id}")
        
        # Convert string to ObjectId for MongoDB query
        from bson import ObjectId
        try:
            object_id = ObjectId(company_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid company ID format"
            )
        
        # Query MongoDB for the company report
        company_doc = await db.startup_profiles.find_one({
            "_id": object_id,
            "status": "completed"
        })
        
        if not company_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Company analysis not found or not completed"
            )
        
        # Extract analysis data
        analysis = company_doc.get("analysis", {})
        
        # Build the response
        report = CompanyReportResponse(
            company_id=company_id,
            company_name=company_doc.get("company_name", "Unknown"),
            company_url=company_doc.get("company_url", ""),
            analysis_date=company_doc.get("created_at", datetime.now(timezone.utc)).isoformat(),
            summary=analysis.get("summary", "No summary available"),
            details={
                "mission": analysis.get("mission", ""),
                "value_proposition": analysis.get("value_proposition", ""),
                "business_model": analysis.get("business_model", ""),
                "key_insights": analysis.get("key_insights", []),
                "website_title": company_doc.get("website_title", ""),
                "meta_description": company_doc.get("meta_description", ""),
                "content_length": company_doc.get("content_length", 0),
                "processing_time_seconds": company_doc.get("processing_time_seconds", 0),
                "embedding_dimension": len(company_doc.get("summary_vector", [])),
                "task_id": company_doc.get("task_id", ""),
                "raw_content_sample": company_doc.get("raw_content_sample", "")
            }
        )
        
        logger.info(f"Retrieved report for company {company_doc.get('company_name', 'Unknown')}")
        return report
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Failed to get company report for {company_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve company report: {str(e)}"
        )


@router.get(
    "/health",
    summary="Health check",
    description="Check if the API, MongoDB, Celery workers, and AI services are healthy.",
    responses={
        200: {"description": "Service is healthy"},
        500: {"description": "Service is unhealthy"}
    }
)
async def health_check(
    db: AsyncIOMotorDatabase = Depends(get_async_database)
) -> Dict[str, Any]:
    """
    Comprehensive health check endpoint.
    
    Returns:
        Dict with health status information for all services
    """
    health_status = {
        "api_status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "services": {}
    }
    
    try:
        # Check MongoDB health
        logger.info("Checking MongoDB health")
        try:
            from app.core.mongo_client import health_check as mongo_health_check
            mongo_result = await mongo_health_check()
            health_status["services"]["mongodb"] = mongo_result
        except Exception as e:
            health_status["services"]["mongodb"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check Celery worker health
        logger.info("Checking Celery worker health")
        try:
            from app.workers.tasks import health_check as worker_health_check
            task = worker_health_check.delay()
            worker_result = task.get(timeout=5.0)
            health_status["services"]["celery_worker"] = {
                "status": "healthy",
                "response": worker_result
            }
        except Exception as e:
            health_status["services"]["celery_worker"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check AI services (Ollama)
        logger.info("Checking AI services health")
        try:
            from app.core.embeddings import test_embeddings_connection
            embeddings_result = await test_embeddings_connection()
            health_status["services"]["ollama_embeddings"] = embeddings_result
        except Exception as e:
            health_status["services"]["ollama_embeddings"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Check LLM service
        try:
            from app.agents.profile_agent import CompanyProfileAgent
            # Quick test of LLM initialization
            agent = CompanyProfileAgent()
            if agent.llm:
                health_status["services"]["ollama_llm"] = {
                    "status": "healthy",
                    "model": agent.llm.model
                }
            else:
                health_status["services"]["ollama_llm"] = {
                    "status": "unhealthy",
                    "error": "LLM not initialized"
                }
        except Exception as e:
            health_status["services"]["ollama_llm"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        # Determine overall health
        unhealthy_services = [
            service for service, status in health_status["services"].items()
            if status.get("status") == "unhealthy"
        ]
        
        if unhealthy_services:
            health_status["overall_status"] = "degraded"
            health_status["unhealthy_services"] = unhealthy_services
            health_status["message"] = f"Some services are unhealthy: {', '.join(unhealthy_services)}"
        else:
            health_status["overall_status"] = "healthy"
            health_status["message"] = "All services are healthy"
        
        return health_status
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health check failed: {str(e)}"
        )

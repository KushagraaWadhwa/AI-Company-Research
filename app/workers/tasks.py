"""
Celery tasks for startup analysis processing.
"""

import time
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from bson import ObjectId
from celery import current_task

from app.workers.celery_app import celery_app
from app.agents.profile_agent import CompanyProfileAgent
from app.core.embeddings import generate_embedding
from app.core.mongo_client import get_sync_database

# Configure logging
logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_startup_analysis")
def run_startup_analysis(
    self, 
    company_name: str, 
    company_url: Optional[str] = None,
    additional_info: Optional[str] = None,
    analysis_type: str = "standard"
) -> Dict[str, Any]:
    """
    Perform comprehensive startup analysis using AI agents.
    
    This task orchestrates the complete analysis workflow:
    1. Company discovery (if no URL provided)
    2. Multi-source data collection
    3. AI analysis using LangChain + Ollama
    4. Vector embedding generation
    5. Data storage in MongoDB
    
    Args:
        company_name: Name of the company to analyze
        company_url: URL of the company website (optional)
        additional_info: Additional context for discovery
        analysis_type: Type of analysis to perform
        
    Returns:
        Dict containing analysis results and MongoDB document ID
    """
    start_time = time.time()
    
    try:
        logger.info(f"🚀 Starting {analysis_type} analysis for {company_name}")
        
        # Determine total steps based on analysis type
        total_steps = 8 if not company_url else 6  # Extra steps for discovery
        if analysis_type == "universal":
            total_steps += 2  # Extra steps for multi-source analysis
        
        # Update task state to indicate processing has started
        self.update_state(
            state="STARTED",
            meta={
                "current_step": "Initializing analysis",
                "progress": 0,
                "total_steps": total_steps,
                "company_name": company_name,
                "company_url": company_url,
                "analysis_type": analysis_type
            }
        )
        
        current_step = 1
        
        # Step 1: Company Discovery (if no URL provided)
        if not company_url:
            # Temporarily disable discovery and use a placeholder URL
            logger.info("Step 1: Company URL discovery (temporarily disabled)")
            self.update_state(
                state="PROGRESS",
                meta={
                    "current_step": "Company URL required for analysis",
                    "progress": current_step,
                    "total_steps": total_steps,
                    "percentage": int((current_step / total_steps) * 100)
                }
            )
            
            # For now, require URL to be provided
            raise Exception("Company URL is required. Company discovery feature is temporarily disabled.")
            
            # TODO: Re-enable discovery after fixing import issues
            # from app.agents.company_discovery_agent import CompanyDiscoveryAgent
            # discovery_agent = CompanyDiscoveryAgent()
            # ... discovery logic ...
            
            current_step += 1
        
        # Initialize the appropriate AI agent based on analysis type
        logger.info(f"Step {current_step}: Initializing {analysis_type} AI agent")
        self.update_state(
            state="PROGRESS",
            meta={
                "current_step": f"Initializing {analysis_type} AI agent",
                "progress": current_step,
                "total_steps": total_steps,
                "percentage": int((current_step / total_steps) * 100)
            }
        )
        
        # Choose agent based on analysis type
        logger.info(f"Initializing {analysis_type} agent")
        
        if analysis_type == "universal":
            from app.agents.universal_data_agent import UniversalDataAgent
            agent = UniversalDataAgent()
            logger.info("✅ UniversalDataAgent initialized for comprehensive multi-source analysis")
        elif analysis_type == "comprehensive":
            from app.agents.multi_source_agent import MultiSourceAnalysisAgent
            agent = MultiSourceAnalysisAgent()
            logger.info("✅ MultiSourceAnalysisAgent initialized for enhanced analysis")
        else:  # standard or any other type defaults to standard
            from app.agents.profile_agent import CompanyProfileAgent
            agent = CompanyProfileAgent()
            logger.info("✅ CompanyProfileAgent initialized for standard analysis")
        
        current_step += 1
        
        # Run analysis based on agent type
        logger.info(f"Step {current_step}: Running {analysis_type} analysis")
        self.update_state(
            state="PROGRESS",
            meta={
                "current_step": f"Running {analysis_type} analysis",
                "progress": current_step,
                "total_steps": total_steps,
                "percentage": int((current_step / total_steps) * 100)
            }
        )
        
        # Run the async agent in the sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            # Run analysis using the appropriate method for each agent type
            if analysis_type == "universal":
                logger.info("🌐 Running universal analysis with multi-source data collection")
                analysis_result = loop.run_until_complete(
                    agent.run_universal_analysis(company_name, company_url)
                )
            elif analysis_type == "comprehensive":
                logger.info("📊 Running comprehensive analysis with enhanced data sources")
                analysis_result = loop.run_until_complete(
                    agent.run_multi_source_analysis(company_name, company_url)
                )
            else:  # standard analysis
                logger.info("📝 Running standard analysis with core company data")
                analysis_result = loop.run_until_complete(agent.run(company_url))
        finally:
            loop.close()
        
        current_step += 1
        
        # Check if analysis was successful
        if analysis_result.get("status") == "error":
            raise Exception(f"Agent analysis failed: {analysis_result.get('error', 'Unknown error')}")
        
        # Step 3: Generate embeddings
        logger.info("Step 3: Generating vector embeddings")
        self.update_state(
            state="PROGRESS",
            meta={
                "current_step": "Generating vector embeddings",
                "progress": 3,
                "total_steps": 6,
                "percentage": 50
            }
        )
        
        # Generate embedding for the summary
        summary_text = analysis_result["analysis"]["summary"]
        try:
            summary_vector = generate_embedding(summary_text)
            logger.info(f"Generated embedding vector of dimension {len(summary_vector)}")
        except Exception as e:
            logger.warning(f"Failed to generate embeddings: {e}")
            summary_vector = []
        
        # Step 4: Connect to MongoDB
        logger.info("Step 4: Connecting to MongoDB")
        self.update_state(
            state="PROGRESS",
            meta={
                "current_step": "Connecting to database",
                "progress": 4,
                "total_steps": 6,
                "percentage": 67
            }
        )
        
        db = get_sync_database()
        collection = db.startup_profiles
        
        # Step 5: Prepare document for storage
        logger.info("Step 5: Preparing document for storage")
        self.update_state(
            state="PROGRESS",
            meta={
                "current_step": "Preparing data for storage",
                "progress": 5,
                "total_steps": 6,
                "percentage": 83
            }
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Create the document to be stored
        document = {
            "company_name": company_name,
            "company_url": company_url,
            "analysis_type": analysis_type,
            "website_title": analysis_result.get("website_title", ""),
            "meta_description": analysis_result.get("meta_description", ""),
            "content_length": analysis_result.get("content_length", 0),
            
            # AI Analysis Results
            "analysis": {
                "summary": analysis_result["analysis"]["summary"],
                "mission": analysis_result["analysis"].get("mission", ""),
                "value_proposition": analysis_result["analysis"].get("value_proposition", ""),
                "business_model": analysis_result["analysis"].get("business_model", ""),
                "key_insights": analysis_result["analysis"].get("key_insights", [])
            },
            
            # Vector embedding for similarity search
            "summary_vector": summary_vector,
            
            # Metadata
            "status": "completed",
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "processing_time_seconds": processing_time,
            "task_id": self.request.id,
            
            # Raw data (truncated for storage efficiency)
            "raw_content_sample": analysis_result.get("raw_content", "")[:2000]
        }
        
        # Step 6: Save to MongoDB
        logger.info("Step 6: Saving analysis to MongoDB")
        self.update_state(
            state="PROGRESS",
            meta={
                "current_step": "Saving analysis to database",
                "progress": 6,
                "total_steps": 6,
                "percentage": 100
            }
        )
        
        # Insert the document (handle duplicates gracefully)
        try:
            insert_result = collection.insert_one(document)
            document_id = str(insert_result.inserted_id)
            logger.info(f"✅ New document created with ID: {document_id}")
        except Exception as insert_error:
            # Handle duplicate key error gracefully
            if "duplicate key error" in str(insert_error) or "E11000" in str(insert_error):
                logger.info(f"Document already exists for {company_url}, updating instead...")
                # Create update document without _id field
                update_document = {k: v for k, v in document.items() if k != '_id'}
                update_document.update({
                    "updated_at": datetime.now(timezone.utc),
                    "task_id": self.request.id,
                    "status": "completed"  # Ensure status is set to completed
                })
                
                # Update existing document
                update_result = collection.update_one(
                    {"company_url": company_url},
                    {"$set": update_document}
                )
                if update_result.matched_count > 0:
                    existing_doc = collection.find_one({"company_url": company_url})
                    document_id = str(existing_doc["_id"])
                    logger.info(f"✅ Updated existing document with ID: {document_id}")
                else:
                    raise insert_error
            else:
                raise insert_error
        
        # Final result
        final_result = {
            "company_name": company_name,
            "company_url": company_url,
            "status": "Analysis Complete",
            "mongodb_id": document_id,
            "summary": analysis_result["analysis"]["summary"],
            "analysis_date": datetime.now(timezone.utc).isoformat(),
            "processing_time_seconds": processing_time,
            "content_length": analysis_result.get("content_length", 0),
            "embedding_dimension": len(summary_vector),
            "details": {
                "mission": analysis_result["analysis"].get("mission", ""),
                "value_proposition": analysis_result["analysis"].get("value_proposition", ""),
                "business_model": analysis_result["analysis"].get("business_model", ""),
                "key_insights": analysis_result["analysis"].get("key_insights", []),
                "website_title": analysis_result.get("website_title", ""),
                "meta_description": analysis_result.get("meta_description", "")
            }
        }
        
        logger.info(f"✅ Analysis completed for {company_name} in {processing_time:.2f}s (ID: {document_id})")
        return final_result
        
    except Exception as exc:
        processing_time = time.time() - start_time
        error_msg = str(exc)
        
        logger.error(f"❌ Analysis failed for {company_name}: {error_msg}")
        
        # Try to save error state to MongoDB
        try:
            db = get_sync_database()
            collection = db.startup_profiles
            
            error_document = {
                "company_name": company_name,
                "company_url": company_url,
                "status": "failed",
                "error": error_msg,
                "created_at": datetime.now(timezone.utc),
                "processing_time_seconds": processing_time,
                "task_id": self.request.id
            }
            
            # Try to update existing document first, then insert if not found
            update_result = collection.update_one(
                {"company_url": company_url},
                {"$set": error_document},
                upsert=True
            )
            
            if update_result.upserted_id:
                logger.info(f"Saved error state to MongoDB: {update_result.upserted_id}")
            else:
                logger.info(f"Updated existing document with error state")
            
        except Exception as db_error:
            logger.error(f"Failed to save error state to MongoDB: {db_error}")
        
        # Update task state to indicate failure
        self.update_state(
            state="FAILURE",
            meta={
                "error": error_msg,
                "company_name": company_name,
                "company_url": company_url,
                "processing_time_seconds": processing_time
            }
        )
        
        # Re-raise the exception to mark task as failed
        raise exc


@celery_app.task(name="health_check")
def health_check() -> Dict[str, str]:
    """
    Simple health check task to verify Celery is working.
    
    Returns:
        Dict with health status
    """
    return {
        "status": "healthy",
        "message": "Celery worker is operational",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

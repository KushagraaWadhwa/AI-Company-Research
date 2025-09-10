"""
Pydantic schemas for API request and response models.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, Field


class AnalysisRequest(BaseModel):
    """Request model for startup analysis."""
    
    company_name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Name of the company to analyze"
    )
    company_url: Optional[HttpUrl] = Field(
        None,
        description="URL of the company website (optional - we can discover it)"
    )
    additional_info: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional context like industry, location, or other details"
    )
    analysis_type: str = Field(
        default="standard",
        description=(
            "Type of analysis to perform:\n"
            "• 'standard' - Core company analysis using primary website data\n"
            "• 'comprehensive' - Enhanced analysis with additional data sources\n"
            "• 'universal' - Most comprehensive analysis from 50+ data sources"
        )
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "company_name": "OpenAI",
                    "company_url": "https://openai.com",
                    "analysis_type": "standard",
                    "description": "Basic analysis using company website data"
                },
                {
                    "company_name": "Stripe",
                    "company_url": "https://stripe.com",
                    "additional_info": "fintech payment processing",
                    "analysis_type": "comprehensive",
                    "description": "Enhanced analysis with multiple data sources"
                },
                {
                    "company_name": "Airbnb",
                    "company_url": "https://airbnb.com",
                    "analysis_type": "universal",
                    "description": "Most comprehensive analysis from 50+ sources"
                }
            ]
        }


class AnalysisTaskResponse(BaseModel):
    """Response model for analysis task creation."""
    
    task_id: str = Field(
        ...,
        description="Unique identifier for the analysis task"
    )
    message: str = Field(
        default="Analysis task created successfully",
        description="Status message"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "12345678-1234-5678-9abc-123456789012",
                "message": "Analysis task created successfully"
            }
        }


class AnalysisStatusResponse(BaseModel):
    """Response model for analysis task status."""
    
    task_id: str = Field(
        ...,
        description="Unique identifier for the analysis task"
    )
    status: str = Field(
        ...,
        description="Current status of the task (PENDING, STARTED, SUCCESS, FAILURE, RETRY, REVOKED)"
    )
    result: Optional[Dict[str, Any]] = Field(
        None,
        description="Task result if completed successfully"
    )
    error: Optional[str] = Field(
        None,
        description="Error message if task failed"
    )
    progress: Optional[Dict[str, Any]] = Field(
        None,
        description="Task progress information"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "12345678-1234-5678-9abc-123456789012",
                "status": "SUCCESS",
                "result": {
                    "company_name": "OpenAI",
                    "status": "Analysis Complete",
                    "summary": "This is a placeholder summary."
                }
            }
        }


class CompanyReportResponse(BaseModel):
    """Response model for company analysis report."""
    
    company_id: str = Field(
        ...,
        description="Unique identifier for the company"
    )
    company_name: str = Field(
        ...,
        description="Name of the company"
    )
    company_url: str = Field(
        ...,
        description="URL of the company website"
    )
    analysis_date: str = Field(
        ...,
        description="Date when the analysis was performed"
    )
    summary: str = Field(
        ...,
        description="Executive summary of the analysis"
    )
    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detailed analysis results"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "company_id": "openai-12345",
                "company_name": "OpenAI",
                "company_url": "https://openai.com",
                "analysis_date": "2024-01-15T10:30:00Z",
                "summary": "OpenAI is a leading AI research company...",
                "details": {
                    "market_analysis": "Strong position in AI market",
                    "technology_stack": ["Python", "TensorFlow", "PyTorch"],
                    "funding_rounds": []
                }
            }
        }


class ErrorResponse(BaseModel):
    """Standard error response model."""
    
    error: str = Field(
        ...,
        description="Error message"
    )
    detail: Optional[str] = Field(
        None,
        description="Additional error details"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "Task not found",
                "detail": "No task found with the provided task_id"
            }
        }

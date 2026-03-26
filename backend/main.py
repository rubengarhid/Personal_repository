"""
FastAPI Main Application
Provides REST API endpoints for CV-LinkedIn comparison.
"""

import torch.utils._pytree as _pytree
if not hasattr(_pytree, 'register_pytree_node'):
    _pytree.register_pytree_node = lambda *args, **kwargs: None
#######################################################################
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import logging

from cv_parser import parse_cv_from_bytes, parse_linkedin_from_bytes
from comparator import CVLinkedInComparator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="CV-LinkedIn Comparator API",
    description="Compare CV documents with LinkedIn profiles",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

comparator: Optional[CVLinkedInComparator] = None


@app.on_event("startup")
async def startup_event():
    """Load the model on startup."""
    global comparator
    logger.info("Loading sentence transformer model...")
    comparator = CVLinkedInComparator()
    logger.info("Model loaded successfully!")


@app.get("/")
async def root():
    return {
        "message": "CV-LinkedIn Comparator API",
        "status": "online",
        "version": "2.0.0"
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "model_loaded": comparator is not None
    }


class CompareResponse(BaseModel):
    """Response model for comparison endpoint."""
    success: bool
    overall_score: float
    section_scores: dict
    discrepancies: list
    skills_comparison: dict
    recommendations: list
    weights: dict


@app.post("/compare", response_model=CompareResponse)
async def compare_cv_linkedin(
    cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)"),
    linkedin_file: UploadFile = File(..., description="LinkedIn profile export (PDF or DOCX)")
):
    """
    Compare a CV with a LinkedIn profile export.

    Both files must be PDF or DOCX format.
    """
    try:
        # Validate CV file type
        if not cv_file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Invalid CV file format. Please upload PDF or DOCX."
            )

        # Validate LinkedIn file type
        if not linkedin_file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Invalid LinkedIn file format. Please upload PDF or DOCX."
            )

        logger.info(f"Processing CV: {cv_file.filename}")
        logger.info(f"Processing LinkedIn file: {linkedin_file.filename}")

        # Read both files
        cv_bytes = await cv_file.read()
        linkedin_bytes = await linkedin_file.read()

        # Parse CV
        logger.info("Parsing CV...")
        cv_data = parse_cv_from_bytes(cv_bytes, cv_file.filename)

        # Parse LinkedIn profile
        logger.info("Parsing LinkedIn profile...")
        linkedin_data = parse_linkedin_from_bytes(linkedin_bytes, linkedin_file.filename)

        # Compare
        logger.info("Comparing CV and LinkedIn profile...")
        comparison_result = comparator.calculate_score(cv_data, linkedin_data)

        # Generate recommendations
        recommendations = comparator.get_recommendations(comparison_result)

        logger.info(f"Comparison complete. Overall score: {comparison_result['overall_score']}%")

        return CompareResponse(
            success=True,
            overall_score=comparison_result['overall_score'],
            section_scores=comparison_result['section_scores'],
            discrepancies=comparison_result['discrepancies'],
            skills_comparison=comparison_result['skills_comparison'],
            recommendations=recommendations,
            weights=comparison_result['weights']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during comparison: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Error processing comparison: {str(e)}"
        )


@app.post("/parse-cv")
async def parse_cv_only(
    cv_file: UploadFile = File(..., description="CV file (PDF or DOCX)")
):
    """Parse a CV file only (for testing/debugging)."""
    try:
        if not cv_file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload PDF or DOCX file."
            )
        
        cv_bytes = await cv_file.read()
        cv_data = parse_cv_from_bytes(cv_bytes, cv_file.filename)
        
        return {
            "success": True,
            "filename": cv_file.filename,
            "sections": {
                "experience": cv_data['experience'][:200] + "..." if len(cv_data['experience']) > 200 else cv_data['experience'],
                "skills": cv_data['skills'][:200] + "..." if len(cv_data['skills']) > 200 else cv_data['skills'],
                "education": cv_data['education'][:200] + "..." if len(cv_data['education']) > 200 else cv_data['education'],
            },
            "extracted_skills": cv_data['extracted_skills']
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing CV: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error parsing CV: {str(e)}")


@app.post("/parse-linkedin")
async def parse_linkedin_only(
    linkedin_file: UploadFile = File(..., description="LinkedIn profile export (PDF or DOCX)")
):
    """Parse a LinkedIn profile file only (for testing/debugging)."""
    try:
        if not linkedin_file.filename.lower().endswith(('.pdf', '.docx')):
            raise HTTPException(
                status_code=400,
                detail="Invalid file format. Please upload PDF or DOCX file."
            )

        linkedin_bytes = await linkedin_file.read()
        linkedin_data = parse_linkedin_from_bytes(linkedin_bytes, linkedin_file.filename)

        return {
            "success": True,
            "filename": linkedin_file.filename,
            "sections": {
                "experience": linkedin_data['experience'][:200] + "..." if len(linkedin_data['experience']) > 200 else linkedin_data['experience'],
                "skills": linkedin_data['skills'][:200] + "..." if len(linkedin_data['skills']) > 200 else linkedin_data['skills'],
                "education": linkedin_data['education'][:200] + "..." if len(linkedin_data['education']) > 200 else linkedin_data['education'],
            },
            "extracted_skills": linkedin_data['extracted_skills']
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error parsing LinkedIn file: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error parsing LinkedIn file: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

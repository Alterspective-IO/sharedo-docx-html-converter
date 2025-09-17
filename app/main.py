"""
Sharedo DOCX to HTML Converter Service
Main FastAPI application
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, Request, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import sys
import time
import json
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))
from sharedo_batch_converter import SharedoBatchConverter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sharedo DOCX to HTML Converter",
    description="Convert Word documents to Sharedo-compatible HTML email templates",
    version="1.0.0",
    contact={
        "name": "Alterspective.io",
        "url": "https://alterspective.io",
        "email": "support@alterspective.io",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    }
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates
templates = Jinja2Templates(directory="app/templates")

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Thread pool for async conversions
executor = ThreadPoolExecutor(max_workers=4)

# In-memory storage for metrics (in production, use Redis or database)
class MetricsStore:
    def __init__(self):
        self.conversions = []
        self.total_conversions = 0
        self.successful_conversions = 0
        self.failed_conversions = 0
        self.total_processing_time = 0
        self.conversion_history = []
        
    def add_conversion(self, result: Dict[str, Any]):
        self.total_conversions += 1
        if result['status'] == 'success':
            self.successful_conversions += 1
        else:
            self.failed_conversions += 1
        
        self.total_processing_time += result.get('processing_time', 0)
        
        # Keep last 100 conversions in history
        self.conversion_history.append(result)
        if len(self.conversion_history) > 100:
            self.conversion_history.pop(0)
    
    def get_metrics(self):
        avg_time = self.total_processing_time / self.total_conversions if self.total_conversions > 0 else 0
        success_rate = (self.successful_conversions / self.total_conversions * 100) if self.total_conversions > 0 else 0
        
        return {
            "total_conversions": self.total_conversions,
            "successful_conversions": self.successful_conversions,
            "failed_conversions": self.failed_conversions,
            "success_rate": round(success_rate, 2),
            "average_processing_time": round(avg_time, 2),
            "recent_conversions": self.conversion_history[-10:]  # Last 10 conversions
        }

metrics_store = MetricsStore()

# Response models
class ConversionResponse(BaseModel):
    """Response model for conversion endpoint"""
    conversion_id: str
    status: str
    message: str
    confidence_score: Optional[float] = None
    html_content: Optional[str] = None
    issues: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    processing_time: Optional[float] = None
    sharedo_elements: Optional[Dict[str, Any]] = None

class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str
    version: str
    uptime: float
    timestamp: str

class MetricsResponse(BaseModel):
    """Response model for metrics endpoint"""
    total_conversions: int
    successful_conversions: int
    failed_conversions: int
    success_rate: float
    average_processing_time: float
    recent_conversions: List[Dict[str, Any]]

# Application startup time
app_start_time = time.time()

@app.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Serve the landing page"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint"""
    uptime = time.time() - app_start_time
    return HealthCheckResponse(
        status="healthy",
        version="1.0.0",
        uptime=round(uptime, 2),
        timestamp=datetime.now().isoformat()
    )

@app.get("/metrics", response_model=MetricsResponse)
async def get_metrics():
    """Get service metrics"""
    return metrics_store.get_metrics()

@app.post("/api/v1/convert", response_model=ConversionResponse)
async def convert_docx(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="DOCX file to convert")
):
    """
    Convert a DOCX file to Sharedo HTML template
    
    - **file**: DOCX file to convert (required)
    
    Returns converted HTML with confidence score and any issues/warnings
    """
    start_time = time.time()
    conversion_id = str(uuid.uuid4())
    
    # Validate file type
    if not file.filename.endswith('.docx'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .docx files are supported."
        )
    
    # Check file size (max 10MB)
    file_size = 0
    contents = await file.read()
    file_size = len(contents)
    
    if file_size > 10 * 1024 * 1024:  # 10MB
        raise HTTPException(
            status_code=400,
            detail="File size exceeds 10MB limit."
        )
    
    # Reset file pointer
    await file.seek(0)
    
    try:
        # Create temporary directory for processing
        with tempfile.TemporaryDirectory() as temp_dir:
            # Save uploaded file
            temp_file_path = Path(temp_dir) / file.filename
            with open(temp_file_path, 'wb') as temp_file:
                temp_file.write(contents)
            
            # Create converter instance
            converter = SharedoBatchConverter(
                input_folder=temp_dir,
                output_folder=temp_dir
            )
            
            # Process single document
            logger.info(f"Processing conversion {conversion_id} for file: {file.filename}")
            file_report = converter.process_single_document(temp_file_path)
            
            # Read generated HTML if successful
            html_content = None
            if file_report['status'] == 'success':
                html_file = Path(temp_dir) / f"{temp_file_path.stem}.html"
                if html_file.exists():
                    html_content = html_file.read_text(encoding='utf-8')
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Prepare response
            response = ConversionResponse(
                conversion_id=conversion_id,
                status=file_report['status'],
                message=f"Conversion {'successful' if file_report['status'] == 'success' else 'failed'}",
                confidence_score=file_report.get('confidence_score'),
                html_content=html_content,
                issues=file_report.get('issues', []),
                warnings=file_report.get('warnings', []),
                processing_time=round(processing_time, 2),
                sharedo_elements=file_report.get('sharedo_elements', {})
            )
            
            # Update metrics
            metrics_data = {
                'conversion_id': conversion_id,
                'filename': file.filename,
                'status': file_report['status'],
                'confidence_score': file_report.get('confidence_score'),
                'processing_time': round(processing_time, 2),
                'timestamp': datetime.now().isoformat()
            }
            metrics_store.add_conversion(metrics_data)
            
            logger.info(f"Conversion {conversion_id} completed with status: {file_report['status']}")
            
            return response
            
    except Exception as e:
        logger.error(f"Error processing conversion {conversion_id}: {str(e)}")
        
        # Update metrics for failure
        metrics_data = {
            'conversion_id': conversion_id,
            'filename': file.filename,
            'status': 'failed',
            'error': str(e),
            'processing_time': round(time.time() - start_time, 2),
            'timestamp': datetime.now().isoformat()
        }
        metrics_store.add_conversion(metrics_data)
        
        raise HTTPException(
            status_code=500,
            detail=f"Conversion failed: {str(e)}"
        )

@app.post("/api/v1/convert/batch")
async def convert_batch(
    files: List[UploadFile] = File(..., description="Multiple DOCX files to convert")
):
    """
    Convert multiple DOCX files to Sharedo HTML templates
    
    - **files**: List of DOCX files to convert (required)
    
    Returns a report with all conversion results
    """
    batch_id = str(uuid.uuid4())
    results = []
    
    for file in files:
        if not file.filename.endswith('.docx'):
            results.append({
                'filename': file.filename,
                'status': 'failed',
                'error': 'Invalid file type'
            })
            continue
        
        try:
            # Process each file
            response = await convert_docx(BackgroundTasks(), file)
            results.append({
                'filename': file.filename,
                'status': response.status,
                'confidence_score': response.confidence_score,
                'conversion_id': response.conversion_id
            })
        except Exception as e:
            results.append({
                'filename': file.filename,
                'status': 'failed',
                'error': str(e)
            })
    
    return {
        'batch_id': batch_id,
        'total_files': len(files),
        'successful': len([r for r in results if r['status'] == 'success']),
        'failed': len([r for r in results if r['status'] == 'failed']),
        'results': results
    }

@app.get("/api/v1/report/{conversion_id}")
async def get_conversion_report(conversion_id: str):
    """
    Get detailed report for a specific conversion
    
    - **conversion_id**: UUID of the conversion
    
    Returns detailed conversion report if available
    """
    # Find conversion in history
    for conversion in metrics_store.conversion_history:
        if conversion.get('conversion_id') == conversion_id:
            return conversion
    
    raise HTTPException(
        status_code=404,
        detail=f"Conversion {conversion_id} not found"
    )

@app.get("/api/v1/sample")
async def download_sample():
    """
    Download a sample DOCX file for testing
    
    Returns a sample DOCX file with Sharedo tags
    """
    sample_file = Path("SUPLC1031.docx")
    if sample_file.exists():
        return FileResponse(
            path=sample_file,
            media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            filename="sample_sharedo_template.docx"
        )
    else:
        raise HTTPException(
            status_code=404,
            detail="Sample file not found"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
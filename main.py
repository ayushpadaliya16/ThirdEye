from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import asyncio
import logging

# Import the forensics modules
from analyzers.osint_engine import run_footprint_analysis
from analyzers.media_forensics import run_image_forensics
from analyzers.face_synthetics import analyze_profile_photo
from analyzers.network_graph import build_network_topology

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Comprehensive OSINT & Forensics API",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProfileRequest(BaseModel):
    username: str
    connections: Optional[list] = [] # List of tuples for network graph

@app.get("/health")
async def health_check():
    return {"status": "Forensics API is operational"}

@app.post("/api/v1/analyze/profile")
async def analyze_profile_route(req: ProfileRequest):
    """Triggers OSINT footprinting and network graph analysis."""
    try:
        # Run analyses concurrently
        osint_task = run_footprint_analysis(req.username)
        # Network graph is synchronous, but we wrap it logically here
        network_data = build_network_topology(req.username, req.connections)
        
        osint_result = await osint_task
        
        return {
            "osint_footprint": osint_result,
            "network_topology": network_data
        }
    except Exception as e:
        logger.error(f"Error in profile analysis: {e}")
        raise HTTPException(status_code=500, detail="Profile analysis failed")

@app.post("/api/v1/analyze/media")
async def analyze_media_route(file: UploadFile = File(...)):
    """Triggers Exif, steganography, and OpenCV synthetic face analysis."""
    try:
        image_bytes = await file.read()
        
        # Execute media and face forensics concurrently using asyncio.gather
        media_result, face_result = await asyncio.gather(
            run_image_forensics(image_bytes),
            analyze_profile_photo(image_bytes)
        )
        
        return {
            "filename": file.filename,
            "media_forensics": media_result,
            "face_synthetics": face_result
        }
    except Exception as e:
        logger.error(f"Error in media analysis: {e}")
        raise HTTPException(status_code=500, detail="Media analysis failed")

@app.post("/api/v1/analyze/comprehensive")
async def analyze_comprehensive_route(
    username: str = Form(...),
    file: Optional[UploadFile] = File(None)
):
    """Unified pipeline accepting username and optional profile photo."""
    try:
        tasks = [run_footprint_analysis(username)]
        
        if file:
            image_bytes = await file.read()
            tasks.extend([
                run_image_forensics(image_bytes),
                analyze_profile_photo(image_bytes)
            ])
            
        results = await asyncio.gather(*tasks)
        
        response = {
            "username": username,
            "osint_footprint": results[0],
            "network_topology": build_network_topology(username, []) # Assuming empty connections for unified route
        }
        
        if file:
            response["media_forensics"] = results[1]
            response["face_synthetics"] = results[2]
            
        return response
    except Exception as e:
        logger.error(f"Error in comprehensive analysis: {e}")
        raise HTTPException(status_code=500, detail="Comprehensive analysis failed")

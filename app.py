from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi.responses import JSONResponse
import shutil
import os
import subprocess
import json
import requests
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

app = FastAPI(title="Waste Image Verification API")

# Pydantic model for JSON requests
class ImageUrlRequest(BaseModel):
    image_url: str

# Path to your existing script
SCRIPT_PATH = Path(__file__).parent / "authenticate_image.py"

# Temporary upload folder
UPLOAD_FOLDER = Path(__file__).parent / "uploads"
UPLOAD_FOLDER.mkdir(exist_ok=True)

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Waste Image Verification API",
        "version": "1.0.0",
        "endpoints": {
            "analyze_image": "/analyze-image/",
            "analyze_image_url": "/analyze-image-url/",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

@app.post("/analyze-image-url/")
async def analyze_image_url(payload: dict):
    """
    Endpoint to analyze waste image from URL (e.g., Cloudinary).
    Accepts: JSON with image_url field
    Returns: JSON with authenticity, confidence_score, and waste_type
    """
    image_url = payload.get("image_url")
    
    # Validate URL
    if not image_url or not image_url.startswith(('http://', 'https://')):
        raise HTTPException(status_code=400, detail="Invalid URL. Must start with http:// or https://")
    
    # Download image from URL
    try:
        response = requests.get(image_url, timeout=30)
        response.raise_for_status()
        
        # Check if it's actually an image
        content_type = response.headers.get('content-type', '').lower()
        if not content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"URL does not point to an image. Content-Type: {content_type}")
        
        # Determine file extension from URL or content type
        if 'jpeg' in content_type or 'jpg' in content_type:
            ext = '.jpg'
        elif 'png' in content_type:
            ext = '.png'
        elif 'webp' in content_type:
            ext = '.webp'
        elif 'gif' in content_type:
            ext = '.gif'
        else:
            ext = '.jpg'  # Default fallback
        
        # Save downloaded image temporarily
        temp_filename = f"temp_image_{hash(image_url) % 10000}{ext}"
        temp_file_path = UPLOAD_FOLDER / temp_filename
        
        with open(temp_file_path, "wb") as f:
            f.write(response.content)
            
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to download image from URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image URL: {str(e)}")

    # Run your existing authenticate_image.py script
    try:
        result = subprocess.run(
            ["python", str(SCRIPT_PATH), "--image", str(temp_file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout

        # Parse JSON from your script
        try:
            json_output = json.loads(output)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to parse JSON from Gemini script", "raw_output": output[:500]}
            )

        return json_output

    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Gemini analysis script failed", "details": e.stderr}
        )
    finally:
        # Clean up downloaded file
        try:
            temp_file_path.unlink()
        except Exception:
            pass

@app.post("/analyze-image/")
async def analyze_image(file: UploadFile = File(...)):
    """
    Endpoint to analyze uploaded waste image.
    Accepts: Multipart file upload
    Returns: JSON with authenticity, confidence_score, and waste_type
    """
    # Validate file type
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

    # Save uploaded file temporarily
    temp_file_path = UPLOAD_FOLDER / file.filename
    with open(temp_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Run your existing authenticate_image.py script
    try:
        result = subprocess.run(
            ["python", str(SCRIPT_PATH), "--image", str(temp_file_path)],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout

        # Parse JSON from your script
        try:
            json_output = json.loads(output)
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=500,
                content={"error": "Failed to parse JSON from Gemini script", "raw_output": output[:500]}
            )

        return json_output

    except subprocess.CalledProcessError as e:
        return JSONResponse(
            status_code=500,
            content={"error": "Gemini analysis script failed", "details": e.stderr}
        )
    finally:
        # Clean up uploaded file
        try:
            temp_file_path.unlink()
        except Exception:
            pass

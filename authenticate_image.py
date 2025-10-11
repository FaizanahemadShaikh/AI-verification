#!/usr/bin/env python3
"""
Gemini Vision API - Waste Image Authentication & Classification

Analyzes waste images using Google's Gemini Vision API to:
1. Flag image as real or fake
2. Classify waste type with confidence score

Requirements:
    pip install google-genai

Usage:
    export GEMINI_API_KEY="your_api_key_here"
    python authenticate_image.py --image path/to/image.jpg
"""

import os
import sys
import json
import argparse
import mimetypes
from typing import Literal, TypedDict
from pathlib import Path

from google import genai
from google.genai import types


# ---------- Default API Key (set here to avoid env var each run) ----------
# Replace the placeholder below with your actual API key.
DEFAULT_API_KEY = "AIzaSyCU3xyGiH_vqXwGRSw_6t77-lG__JlISxE"


# ---------- Type Definitions for Structured Output ----------

Authenticity = Literal["real", "fake"]

WasteType = Literal[
    "e_waste",
    "domestic_waste",
    "construction_waste",
    "biomedical_waste",
    "industrial_waste",
    "agricultural_waste",
    "hazardous_waste",
    "plastic_waste",
    "litter",
    "unknown",
]


class WasteAnalysis(TypedDict):
    """Schema for Gemini's structured JSON response."""
    authenticity: Authenticity
    confidence_score: float
    waste_type: WasteType


# ---------- Optimized Vision Prompt ----------

VISION_ANALYSIS_PROMPT = """You are an advanced AI image analyzer specialized in environmental waste detection and authenticity verification.

You must strictly follow the following decision rules and output schema.

---------------------
🎯 OUTPUT JSON SCHEMA
---------------------
{
  "authenticity": "real|fake",
  "confidence_score": float,
  "waste_type": "e_waste|domestic_waste|construction_waste|biomedical_waste|industrial_waste|agricultural_waste|hazardous_waste|plastic_waste|litter|unknown"
}

---------------------
🧩 ANALYSIS INSTRUCTIONS
---------------------

STEP 1: IMAGE VALIDATION
- Determine whether the image is a *real photograph* or *AI-generated/edited/fake*.
- Examine lighting, shadows, texture, noise patterns, reflections, and geometry consistency.
- If image is *AI-generated, edited, digitally composited, artistic, or not a real photograph*:
  → Immediately output:
    {
      "authenticity": "fake",
      "confidence_score": 0,
      "waste_type": "unknown"
    }
  → Stop further analysis.

STEP 2: WASTE CONTENT CHECK
- If the image is real, check whether it contains *visible waste materials*.
- Waste materials include litter, garbage, e-waste, plastics, construction debris, biomedical waste, etc.
- If the image does NOT contain any waste (e.g. humans, animals, landscapes, objects, etc.):
  → Immediately output:
    {
      "authenticity": "fake",
      "confidence_score": 0,
      "waste_type": "unknown"
    }
  → Stop further analysis.

STEP 3: FULL ANALYSIS (ONLY IF REAL WASTE SCENE)
- If the image is both *real* AND *contains visible waste*, then:
  1. Set "authenticity" = "real"
  2. Estimate "confidence_score" (0–100) based on image realism and clarity
  3. Identify primary "waste_type" from one of the predefined categories:
     - e_waste
     - domestic_waste
     - construction_waste
     - biomedical_waste
     - industrial_waste
     - agricultural_waste
     - hazardous_waste
     - plastic_waste
     - litter
     - unknown (only if unclear)

---------------------
⚙️ OUTPUT RULES
---------------------
- Output must be *pure JSON only* (no markdown, no explanations).
- confidence_score must always be numeric (float between 0–100).
- Always include all three fields.
- If image is rejected, always use:
  {
    "authenticity": "fake",
    "confidence_score": 0,
    "waste_type": "unknown"
  }

"""


# ---------- Image Loading ----------

def load_image_as_part(image_path: str) -> types.Part:
    """
    Load an image file and convert to Gemini API Part format.
    
    Args:
        image_path: Path to image file
        
    Returns:
        types.Part object containing image data
        
    Raises:
        FileNotFoundError: If image file doesn't exist
        IOError: If file cannot be read
    """
    path = Path(image_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Image file not found: {image_path}")
    
    if not path.is_file():
        raise IOError(f"Path is not a file: {image_path}")
    
    # Determine MIME type
    mime_type, _ = mimetypes.guess_type(str(path))
    if mime_type is None or not mime_type.startswith("image/"):
        mime_type = "image/jpeg"  # Default fallback
    
    # Read image data
    with open(path, "rb") as f:
        image_data = f.read()
    
    return types.Part.from_bytes(data=image_data, mime_type=mime_type)


# ---------- Main Execution ----------

def main():
    """Main entry point for waste image authentication."""
    
    parser = argparse.ArgumentParser(
        description="Authenticate and classify waste images using Gemini Vision API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --image waste_sample.jpg
  %(prog)s --image photo.png --model gemini-2.5-flash
  %(prog)s --image test.jpg --temperature 0.2 --api-key YOUR_KEY
        """
    )
    
    parser.add_argument(
        "--image",
        required=True,
        help="Path to the input image file (JPEG, PNG, WebP, etc.)"
    )
    
    parser.add_argument(
        "--model",
        default="gemini-2.5-flash",
        help="Gemini model to use (default: gemini-2.5-flash)"
    )
    
    parser.add_argument(
        "--api-key",
        default=os.getenv("GEMINI_API_KEY") or DEFAULT_API_KEY,
        help="Gemini API key (defaults to GEMINI_API_KEY environment variable)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature 0.0-2.0 (default: 0.0 for deterministic output)"
    )
    
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print JSON output with indentation"
    )
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key:
        error_response = {
            "error": "Missing API key",
            "message": "Set DEFAULT_API_KEY in authenticate_image.py, or set GEMINI_API_KEY, or pass --api-key",
            "help": "Get your API key from https://aistudio.google.com/apikey",
            "debug": {
                "env_var": os.getenv("GEMINI_API_KEY"),
                "default_key": DEFAULT_API_KEY[:10] + "..." if DEFAULT_API_KEY else "None"
            }
        }
        print(json.dumps(error_response, indent=2))
        sys.exit(2)
    
    # Initialize Gemini client
    try:
        client = genai.Client(api_key=args.api_key)
    except Exception as e:
        print(json.dumps({"error": "Failed to initialize Gemini client", "details": str(e)}))
        sys.exit(1)
    
    # Load and validate image
    try:
        image_part = load_image_as_part(args.image)
    except FileNotFoundError as e:
        print(json.dumps({"error": "Image file not found", "path": args.image}))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": "Failed to load image", "details": str(e)}))
        sys.exit(1)
    
    # Configure generation parameters
    config = types.GenerateContentConfig(
        temperature=args.temperature,
        response_mime_type="application/json",
    )
    
    # Send request to Gemini Vision API
    try:
        response = client.models.generate_content(
            model=args.model,
            contents=[VISION_ANALYSIS_PROMPT, image_part],
            config=config,
        )
    except Exception as e:
        error_details = {
            "error": "Gemini API request failed",
            "model": args.model,
            "details": str(e)
        }
        print(json.dumps(error_details, indent=2))
        sys.exit(1)
    
    # Parse and validate JSON response
    try:
        result = json.loads(response.text)
        
        # Output formatting
        indent = 2 if args.pretty else None
        print(json.dumps(result, indent=indent, ensure_ascii=False))
        
    except json.JSONDecodeError as e:
        fallback_response = {
            "error": "Invalid JSON response from Gemini",
            "parse_error": str(e),
            "raw_response": response.text[:500]  # First 500 chars for debugging
        }
        print(json.dumps(fallback_response, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

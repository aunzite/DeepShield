"""
DeepShield Backend: hackathon MVP — fast, stable, no heavy ML.

POST /analyze-image: OpenCV Haar Cascade face detection + heuristic scoring (blur, edge, entropy).
POST /analyze-headline: Rule-based manipulation scoring (keywords, caps, punctuation).

No HuggingFace. No torch. No model downloads. No blocking the event loop.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from services.headline_service import analyze_headline
from services.image_service import analyze_image

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 5


def _preload_face_detector() -> None:
    """Load OpenCV face detector once at startup. Lightweight, no downloads."""
    import sys
    try:
        print("DeepShield: Loading face detector (OpenCV Haar Cascade)...", flush=True)
        from services.face_detection import _detector
        _detector()
        print("DeepShield: Face detector ready.", flush=True)
    except Exception as e:
        print(f"DeepShield: Face detector failed: {e}", file=sys.stderr, flush=True)
    print("DeepShield: Startup complete. No heavy models.", flush=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload only OpenCV face detector (fast). Run in executor to avoid blocking."""
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, _preload_face_detector)
    yield


class HeadlineRequest(BaseModel):
    headline: str = Field(..., min_length=1, description="Headline to analyze")


class ImageAnalysisResponse(BaseModel):
    real_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    fake_probability: Optional[float] = Field(None, ge=0.0, le=1.0)
    confidence_level: Optional[str] = None
    error: Optional[str] = None


class HeadlineAnalysisResponse(BaseModel):
    manipulation_score: float = Field(..., ge=0.0, le=1.0)
    risk_level: str
    flagged_phrases: List[str]
    summary: str
    clickbait_score: int = Field(..., ge=0)
    matches: List[Dict[str, Any]] = Field(default_factory=list)
    category_breakdown: Dict[str, int] = Field(default_factory=dict)


app = FastAPI(
    title="DeepShield Backend",
    description="Lightweight deepfake/heuristic image analysis and headline manipulation scoring.",
    version="2.0.0",
    lifespan=lifespan,
)

origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["health"])
def health_check() -> dict:
    return {"status": "ok", "service": "DeepShield backend"}


@app.post("/analyze-image", tags=["analysis"])
async def analyze_image_endpoint(file: UploadFile = File(...)) -> JSONResponse:
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Uploaded file must be an image.")
    try:
        file_bytes = await file.read()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Failed to read uploaded file.") from exc

    loop = asyncio.get_running_loop()
    try:
        result = await asyncio.wait_for(
            loop.run_in_executor(None, lambda: analyze_image(file_bytes)),
            timeout=REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Analysis timed out.") from None
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve)) from ve
    except Exception as exc:
        logger.exception("Image analysis failed")
        raise HTTPException(status_code=500, detail="Analysis failed.") from exc

    return JSONResponse(content=result)


@app.post("/analyze-headline", response_model=HeadlineAnalysisResponse, tags=["analysis"])
async def analyze_headline_endpoint(payload: HeadlineRequest) -> JSONResponse:
    text = payload.headline.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Headline cannot be empty.")
    try:
        result = await asyncio.wait_for(
            asyncio.get_running_loop().run_in_executor(
                None, lambda: analyze_headline(text)
            ),
            timeout=REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="Analysis timed out.") from None
    except Exception as exc:
        logger.exception("Headline analysis failed")
        raise HTTPException(status_code=500, detail="Analysis failed.") from exc
    return JSONResponse(content=result)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=False)

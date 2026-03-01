# Deepfake Detection Pipeline

This document describes the deepfake image detection pipeline used by DeepShield.

## Overview

The pipeline is **face-first** and uses a **deepfake-trained** classifier:

1. **Load image** and convert to RGB (full resolution).
2. **Face detection** – RetinaFace runs on the full-resolution image for robust detection of frontal and in-the-wild faces.
3. **Select largest face** – If multiple faces are detected, the largest bounding box is chosen.
4. **Crop with padding** – The face region is cropped with a small padding (10% of box size) and clamped to image bounds.
5. **Resize & normalize** – The cropped face is resized to the model input size (224×224) and normalized by the deepfake model’s processor.
6. **Inference** – A HuggingFace model trained for real vs. fake (deepfake) face classification runs on CPU.

If **no face** is detected, the API returns:

```json
{ "error": "No face detected. Ensure a clear frontal human face is visible." }
```

On success it returns:

```json
{
  "real_probability": 0.92,
  "fake_probability": 0.08,
  "confidence_level": "High"
}
```

## Components

| Component | Role |
|-----------|------|
| `services/face_detector.py` | RetinaFace face detection on full-resolution image; returns largest face crop with padding or `None`. |
| `models/deepfake_model.py` | Loads `dima806/deepfake_vs_real_image_detection` (ViT 224×224), runs on CPU. |
| `services/image_service.py` | Orchestrates: load RGB → detect face → crop with padding → run deepfake model → return probs or error. |

## Debug logging

When the face detector runs, it logs (at INFO level):

- **Number of faces detected**
- **Bounding box coordinates** (x1, y1, x2, y2) for each face
- **Detection confidence** per face

Example:

```
Face detection: 2 face(s) detected
  face_1: bbox=(x1=120, y1=80, x2=380, y2=400), confidence=0.9821
  face_2: bbox=(x1=400, y1=90, x2=620, y2=410), confidence=0.8756
```

To see these messages, ensure the application’s logging level is set to INFO or lower (e.g. in your run configuration or environment).

## Requirements

- Python 3.8+
- See `requirements.txt`. Key dependencies:
  - **retina-face** – RetinaFace face detection (pulls in TensorFlow and OpenCV)
  - **transformers**, **torch** – deepfake classifier
  - **pillow** – image loading and cropping

## Installation

1. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   .venv\Scripts\activate          # Windows
   # source .venv/bin/activate     # Linux/macOS
   ```

2. Install dependencies:

   ```bash
   cd deep-shield-backend
   pip install -r requirements.txt
   ```

3. First run will download RetinaFace weights and the HuggingFace deepfake model; ensure you have network access.

**Note:** `retina-face` depends on TensorFlow and OpenCV. On headless servers you can install `opencv-python-headless` before `retina-face` if you want to avoid GUI-related OpenCV dependencies.

## Running the backend

```bash
cd deep-shield-backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

On startup the app will:

1. Load the face detector (RetinaFace).
2. Load the deepfake model from HuggingFace.
3. Load the text/headline model.

All inference runs on **CPU** by default.

## API

- **POST /analyze-image**  
  - Body: multipart form with `file` (image).  
  - Success: `200` with `real_probability`, `fake_probability`, `confidence_level`.  
  - No face: `200` with `error` only.  
  - Invalid image: `400`.  
  - Server error: `500`.

## Model choice

The current classifier is **dima806/deepfake_vs_real_image_detection** (ViT fine-tuned for real vs. fake faces). You can switch to another HuggingFace image classifier by changing `DEEPFAKE_MODEL_NAME` in `models/deepfake_model.py` and matching input size and normalization to that model’s processor.

## Production notes

- Face detection and deepfake inference run on CPU.
- Models are cached in process (lazy load on first request; optional preload at startup).
- For “no face” cases the API returns a clear error message instead of a score.
- RetinaFace uses a confidence threshold of 0.5 by default; you can adjust `DETECT_THRESHOLD` in `services/face_detector.py` (lower = more recall, higher = more precision).

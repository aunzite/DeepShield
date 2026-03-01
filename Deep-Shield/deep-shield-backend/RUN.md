# DeepShield Backend – Run Instructions

## Image analysis pipeline (deepfake)

1. **Load image** from upload, convert to RGB (full resolution).
2. **Face detection** on full-resolution image (MediaPipe).
3. **Crop** largest face with 10% padding.
4. **Resize** cropped face to 128×128, normalize, run lightweight CNN.
5. **Response**: `real_probability`, `fake_probability`, `confidence_level`.

- No face → `{ "error": "No clear frontal human face detected." }`.
- Model loads **once at startup**; no downloads during requests. CPU only.

## Setup

```bash
cd deep-shield-backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # Windows PowerShell
# source .venv/bin/activate     # Linux/macOS
pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```bash
# From deep-shield-backend, with venv activated
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- **POST /analyze-image**: multipart form with `file` (image). Returns `real_probability`, `fake_probability`, `confidence_level`, or `error`.  
- 30s timeout; inference runs in a thread pool (does not block the event loop).

## Modules

| File | Role |
|------|------|
| `services/face_detection.py` | MediaPipe face detection; full-res RGB; largest face; 10% padding. |
| `services/model.py` | Lightweight PyTorch CNN placeholder (real/fake logits); loaded once at startup. |
| `services/inference.py` | Load → detect → crop → preprocess → model → response. |
| `main.py` | FastAPI app; preloads models at startup; POST /analyze-image with timeout. |

All image inference runs on **CPU**. No HuggingFace or GPU for the image pipeline.

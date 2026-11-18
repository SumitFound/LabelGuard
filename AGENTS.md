# LabelGuard

## Project goal
Check Indian packaged-commodity label images against configurable Legal Metrology rules, flagging uncertain/unverified requirements for review.

## Stack
Python 3.11, FastAPI, Uvicorn, OpenCV, Pillow, RapidOCR, pyzbar, SQLAlchemy/SQLite, fpdf2, pytest. CPU only; OCR isolated behind `ocr(image)`.

## Folder map
- `app/main.py`: API endpoints
- `app/pipeline.py`: image quality, deskew, contrast, OCR, annotation
- `app/extract.py`: text field extraction
- `app/engine.py`: configurable rule checks and scoring
- `app/db.py`: SQLite persistence
- `app/report.py`: PDF reports
- `rules/rules.json`: rule definitions
- `scripts/make_samples.py`: synthetic labels
- `sample_images/`: generated examples
- `tests/`: extraction and engine tests

## Run
`pip install -r requirements.txt`
`python scripts/make_samples.py`
`uvicorn app.main:app --reload`
`pytest`

## Status
- Phase 1: Complete. Samples generated; 20 tests pass; Uvicorn startup verified with Python 3.11. `pip` was unavailable as a direct command, so dependencies were installed and exercised through `uv`.
- Phase 2: Complete. Responsive static frontend, `/api/samples`, scan detail endpoint, and SDG impact mapping added. Live curl smoke checks returned HTTP 200 for `/`, `/api/samples`, and `/api/scan` with a generated label image.
- Phase 3: Evaluation script processed all six labeled synthetic images; metrics and confusion plot generated; report written. Exact-verdict accuracy was 0.0%; average processing time was 2.338 seconds per image.

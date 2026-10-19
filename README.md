# Lecture Highlighter

Upload a lecture. Get chapters, study notes, and a shareable clip for each chapter.

**Pipeline:** upload → Cloudinary → Whisper transcript → LangGraph chaptering → Cloudinary clip URLs (`start_offset` / `end_offset`) → React dashboard.

## Run it

Backend (needs ffmpeg for some formats):

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill in Cloudinary + LLM keys
uvicorn app.main:app --reload --port 8000
```

Frontend:

```bash
cd frontend
npm install
npm run dev                 # http://localhost:5173
```

## Notes
- No `LLM_API_KEY`? It still runs with plain "Part N" chapters, so you can test the Cloudinary and Whisper steps first.
- Cloudinary free plans cap video uploads (about 100 MB). Use 5-10 minute demo lectures.
- Set `WHISPER_MODEL=tiny` for fast CPU demos.
- `av<19` is pinned for compatibility with the installed `faster-whisper` version.

## Errors and troubleshooting
- Upload and processing failures show actionable messages in the app. For the detailed exception, check the terminal running the backend (`uvicorn`); raw exception details are kept out of the user-facing message.
- If you see `open() got an unexpected keyword argument 'metadata_errors'`, install the backend dependencies again with `pip install -r requirements.txt`. This installs the compatible PyAV version.
- If the app cannot connect to the backend, make sure `uvicorn` is running on port 8000 and the frontend is running on port 5173.

## Structure
```
backend/app/
  routes/lectures.py          upload + read endpoints
  services/cloudinary_svc.py  upload and clip URLs
  services/transcribe.py      faster-whisper
  services/chaptering.py      LangGraph: split -> detect topics -> title/summarize -> validate
  services/pipeline.py        runs the full job in the background
frontend/src/pages/           Home (upload), Lecture (player, timeline, chapters, notes)
```

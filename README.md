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

## Deploy to Render

The included `render.yaml` deploys the frontend and API together as one Docker
web service. Lecture records are stored in SQLite on a persistent disk. This
configuration uses Render's paid Starter service and a 1 GB disk; a free
ephemeral service would lose its database when restarted or redeployed.

1. Push this repository to GitHub and create a new Blueprint on Render for it.
2. Set the prompted `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and
   `CLOUDINARY_API_SECRET` values in Render. `LLM_API_KEY` is optional; without
   it, chaptering falls back to plain "Part N" chapters.
3. Deploy the Blueprint and open the generated `onrender.com` URL.

Keep these credentials in Render's environment settings, not in Git or chat.
The deployment uses the smaller `tiny` Whisper model to limit CPU and memory
usage; it is slower and less accurate than larger models. Keep test lectures
small, especially when deploying under a host's upload-size limit.

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

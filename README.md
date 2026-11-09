# ClipGenius AI starter

Local prototype for processing videos you own or are authorized to edit.

## Requirements
- Python 3.10+
- FFmpeg and ffprobe installed and available on PATH

## Run
```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
Open http://127.0.0.1:8000

Optional captions: `pip install faster-whisper`. This prototype creates evenly spaced clips; AI highlight selection and social publishing are future milestones. Only process videos you own or have permission to use. Social publishing requires each platform's official API authorization.

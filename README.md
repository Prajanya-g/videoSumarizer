# 🎬 Video Summarizer Web App

**Goal:** Upload a video → generate transcript → pick the most important parts → output highlights (concat video or jump-to timestamps).
Think: *“YouTube highlights generator for long podcasts.”*

This is a **functionality-first MVP** — minimal UI, but the full processing pipeline works end-to-end.

---

## ✨ Features

* **Video upload** (via web UI)
* **Automatic transcription** using Whisper (or Faster-Whisper)
* **Highlight detection** with two strategies:

  * **LLM ranking** (uses GPT/local model to pick key moments)
  * **TextRank fallback** (no LLM required)
* **Smart segment selection** (merge nearby clips, enforce min/max lengths, greedy target fitting)
* **Highlight reel export** with FFmpeg (reencoded for browser-safe playback)
* **Jump-to JSON** so user can click timestamps in the player
* **Subtitles (SRT)** + **thumbnail** generation
* **Simple frontend** (HTML + JS) to upload and view results

---

## 🏗️ Project Structure

```
video-summarizer/
├─ backend/
│  ├─ main.py               # FastAPI endpoints
│  ├─ pipeline.py           # Orchestrates processing steps
│  ├─ transcribe.py         # Whisper wrapper
│  ├─ ranker_llm.py         # LLM-based importance scoring
│  ├─ ranker_textrank.py    # TextRank fallback
│  ├─ select_segments.py    # Greedy highlight selection
│  ├─ render.py             # FFmpeg trimming + concat
│  ├─ storage.py            # Paths + job state
│  └─ utils.py              # Helpers
├─ frontend/
│  ├─ index.html            # Minimal UI
│  └─ script.js             # Calls backend
├─ data/
│  └─ jobs/{job_id}/...     # Input/output files per job
├─ requirements.txt
└─ README.md
```

---

## ⚙️ Installation

### 1. Clone & install dependencies

```bash
git clone https://github.com/yourname/video-summarizer.git
cd video-summarizer
pip install -r requirements.txt
```

### 2. Install system dependencies

You need **FFmpeg** installed and available in `$PATH`.
Check:

```bash
ffmpeg -version
```

If not installed:

* macOS: `brew install ffmpeg`
* Ubuntu: `sudo apt install ffmpeg`

---

## 🚀 Running the App

### 1. Start backend

```bash
uvicorn backend.main:app --reload --port 8000
```

### 2. Open frontend

* Open `frontend/index.html` in your browser (or serve it with VS Code’s Live Server).
* By default, it expects backend at `http://localhost:8000`.

---

## 🔄 Workflow

1. **Upload video** (choose file + target duration in seconds).
2. **Pipeline runs automatically**:

   * Extracts audio
   * Transcribes with Whisper → `transcript.json` + `transcript.srt`
   * Ranks segments → `highlights.json`
   * Selects best segments fitting target duration
   * Renders:

     * `highlights.mp4` (concatenated reel)
     * `jump_to.json` (for in-video navigation)
     * `thumb.jpg` (preview image)
3. **Fetch result** → UI shows player with highlight video or clickable timestamps.

---

## 📂 Example Job Output

Inside `data/jobs/12345/`:

```
input.mp4
audio.wav
transcript.json
transcript.srt
highlights.json
jump_to.json
highlights.mp4
thumb.jpg
result.json
```

`highlights.json` (LLM/TextRank output):

```json
{
  "highlights": [
    {
      "start": 122.80,
      "end": 135.30,
      "score": 0.92,
      "label": "Thesis statement"
    },
    {
      "start": 410.00,
      "end": 420.50,
      "score": 0.85,
      "label": "Key statistic"
    }
  ]
}
```

---

## 🔑 Key Endpoints (FastAPI)

* `POST /upload`

  * Params: `file` (video), `target_seconds` (int, default 60)
  * Returns: `{ "job_id": "abc123" }`

* `GET /result/{job_id}`

  * Returns JSON with status + file URLs
  * Example:

    ```json
    {
      "status": "done",
      "video_url": "/jobs/abc123/highlights.mp4",
      "jump_to": { "highlights": [...] },
      "thumbnail_url": "/jobs/abc123/thumb.jpg",
      "srt_url": "/jobs/abc123/transcript.srt"
    }
    ```

---

## 🧠 LLM Integration

The highlight selector can use any LLM (local or API).

Prompt template (used in `ranker_llm.py`):

```
You are selecting highlights from a video transcript with timestamps.
Goal: pick the most informative moments so a viewer gets the gist within {target_seconds}s.
Return STRICT JSON:
{"highlights":[{"start":float,"end":float,"score":0.0-1.0,"label":"short"}]}
```

If LLM fails → fallback to **TextRank**.

---

## ⚡ Roadmap (Optional Extensions)

* Burn subtitles onto highlight reel (`ffmpeg -vf subtitles=...`)
* YouTube-ready **chapters.txt**
* Multi-video batch mode
* Speaker diarization (separate speakers before ranking)

---

## 🧪 Quick Test

```bash
# take a short video
cp sample.mp4 data/jobs/test/input.mp4

# run pipeline manually
python -m backend.pipeline test 60

# check output in data/jobs/test/
```

---

## 📝 License

MIT — free to use and modify.

---


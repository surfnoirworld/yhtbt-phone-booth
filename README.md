# YHTBT Phone Booth — Live Voice Agent

**A real-time voice agent that lives inside a phone directory. Dial 100 and someone answers.**

Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) · Surf Noir Studio · 2026

---

## What Is This

[youhadtobethere.life](https://youhadtobethere.life) is a phone directory built around the album *You Had to Be There* by Cam Murdoch. Each number plays a song or a real voicemail from Cam's journey — leaving home, traveling the world, and coming back changed.

Number 100 is different. When you dial it, a real-time voice agent named **Aza Fre** picks up. She's a 22-year-old travel agent from Nearstalgia Bay who found Cam's directory and wants you to go through it with her. She recruits you, sends you to specific numbers, and when you call back she responds to what you actually heard. The conversation is natural, interruptible, and contextually aware.

It is not a chatbot. It is a phone call.

## Live Demo

**Call Aza:** [youhadtobethere.life](https://youhadtobethere.life) → Dial 100

**Backend health check:** [yhtbt-phone-booth-594415785090.us-east1.run.app](https://yhtbt-phone-booth-594415785090.us-east1.run.app)

## Architecture

```
User's Browser (youhadtobethere.life on Base44)
    ↕ WebSocket (wss://)
Google Cloud Run (FastAPI + ADK)
    ↕ Google Cloud Firestore (session tracking)
    ↕ ADK Runner + LiveRequestQueue
        ↕ Gemini Live API (native audio model)
```

1. User dials 100 on the phone directory
2. Browser requests mic permission, opens WebSocket to Cloud Run
3. Cloud Run fetches caller history from Firestore
4. Injects session context into ADK streaming session
5. Gemini Live API opens with Aza's full character persona
6. Audio streams bidirectionally — user speaks, Aza responds in real time
7. Call events logged to Firestore for session persistence

## Tech Stack

| Component | Technology |
|---|---|
| Agent Framework | Google Agent Development Kit (ADK) |
| Voice Model | Gemini 2.5 Flash Native Audio via Gemini Live API |
| Backend | Python + FastAPI with WebSocket streaming |
| Hosting | Google Cloud Run |
| Session Storage | Google Cloud Firestore |
| Frontend | Base44 (youhadtobethere.life) |
| API Key Management | Google AI Studio |

## Project Structure

```
adk-streaming/
├── Dockerfile
├── requirements.txt
└── app/
    ├── .env
    ├── main.py                    # FastAPI server with WebSocket streaming
    ├── caller_store.py            # Firestore session tracking
    └── aza_agent/
        ├── __init__.py
        ├── agent.py               # ADK agent definition
        └── prompts/
            ├── character_layer.txt     # Aza's persona and voice
            ├── navigation_layer.txt    # 11-cycle story progression
            └── voicemail_transcripts.txt  # Reference material for reactions
```

## Spin Up Locally

### Prerequisites
- Python 3.10+
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- Google Cloud project with Firestore enabled (optional — app works without it)

### Setup

```bash
# Clone the repo
git clone https://github.com/YOUR_USERNAME/yhtbt-phone-booth.git
cd yhtbt-phone-booth/adk-streaming

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cd app
echo 'GOOGLE_GENAI_USE_VERTEXAI=FALSE' > .env
echo 'GOOGLE_API_KEY=your_api_key_here' >> .env
```

### Run with ADK Dev UI (voice testing)

```bash
cd app
export SSL_CERT_FILE=$(python -m certifi)
adk web
```

Opens at http://localhost:8000. Select `aza_agent`, click the microphone, and talk.

### Run with FastAPI Server (production mode)

```bash
cd app
python main.py
```

Starts at http://localhost:8080. WebSocket endpoint at `/ws/{caller_id}`.

## Deploy to Google Cloud Run

```bash
cd adk-streaming

gcloud run deploy yhtbt-phone-booth --source . --region us-east1 --allow-unauthenticated --set-env-vars "GOOGLE_API_KEY=your_key,GOOGLE_GENAI_USE_VERTEXAI=FALSE" --memory 1Gi --timeout 300 --session-affinity
```

## The Agent

### Who She Is
Aza Fre, 22, works at Excursion Club in Nearstalgia Bay. She found Cam's travel videos, got fascinated by the journey, dug deeper into the phone directory, and eventually reached Cam and invited him to Nearstalgia Bay. Now she wants other people to experience the directory.

### What She Does
- Answers expecting someone else, reacts when she gets a stranger
- Recruits the caller to listen to specific numbers on the directory
- Responds to their interpretation of what they heard — no wrong answers
- Moves them through 11 narrative cycles with branching paths
- At the end, invites them to Nearstalgia Bay (number 757)

### What She Won't Do
- Confirm there's a game
- Break character
- Give numbers without real engagement first
- Say where she's from
- Sound like an assistant

### The Story Structure
11 cycles tracing Cam's journey from leaving home to coming back changed. Two branching points (Cycles 2 and 5) where the caller's interpretation determines which path they take. Every answer is valid. Nobody gets stuck.

## Audio Specs

| Direction | Format | Sample Rate |
|---|---|---|
| User → Server | Raw PCM, 16-bit, mono, little-endian | 16kHz |
| Server → User | Raw PCM, 16-bit, mono, little-endian (via base64 JSON) | 16kHz |

## Hackathon Category

**Live Agents** — Real-time interaction with audio. An agent users can talk to naturally and interrupt.

### Mandatory Tech Used
- Gemini Live API (native audio model)
- Google Agent Development Kit (ADK)
- Google Cloud Run
- Google Cloud Firestore

### Judging Criteria Addressed
- **Innovation & Multimodal UX (40%):** Fully realized character with distinct persona, 11-cycle branching narrative, persistent session memory, lives inside an existing ARG campaign
- **Technical Implementation (30%):** ADK with Gemini Live API, Firestore session tracking, Cloud Run deployment, WebSocket bidirectional audio streaming
- **Demo & Presentation (30%):** Live demo through actual phone directory site, real conversation with barge-in support

## Credits

**Narrative Design:** Surf Noir Studio
**Album:** *You Had to Be There* by Cam Murdoch
**Campaign:** [youhadtobethere.life](https://youhadtobethere.life)
**Agent Framework:** [Google Agent Development Kit](https://google.github.io/adk-docs/)

---

*Surf Noir Studio · 2026*
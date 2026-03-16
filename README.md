# YHTBT Phone Booth — Live Voice Agent

**A real-time voice agent that lives inside a phone directory. Dial 100 and someone answers.**

Built for the [Gemini Live Agent Challenge](https://geminiliveagentchallenge.devpost.com/) · Surf Noir Studio · 2026

---

## What Is This

[youhadtobethere.life](https://youhadtobethere.life) is a phone directory built around the album *You Had to Be There* by Cam Murdoch. Each number plays a song or a real voicemail from Cam's journey — leaving home, traveling the world, and coming back changed.

Number 100 is different. When you dial it, a real-time voice agent named **Aza Fre** picks up. She's a 22-year-old travel agent from Nearstalgia Bay who found Cam's directory and is trying to piece together where Cam went. She recruits you to go through the directory with her, sends you to specific numbers, and when you call back she responds to what you actually heard. Over time she starts asking about your life too — not just Cam's. The conversation is natural, interruptible, and contextually aware.

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
├── deploy.sh                      # Automated Cloud Run deployment script
├── yhtbt-architecture-diagram.svg
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

## Reproduce Locally — Step by Step

### Prerequisites
- Python 3.10 or later
- pip
- A Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)
- A microphone and a modern browser (Chrome recommended)
- Google Cloud project with Firestore enabled (optional — the agent works without it, session memory just won't persist)

### 1. Clone and set up environment

```bash
git clone https://github.com/surfnoirworld/yhtbt-phone-booth.git
cd yhtbt-phone-booth/adk-streaming

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure your API key

```bash
cd app
echo 'GOOGLE_GENAI_USE_VERTEXAI=FALSE' > .env
echo 'GOOGLE_API_KEY=your_api_key_here' >> .env
```

Replace `your_api_key_here` with your actual Gemini API key from Google AI Studio.

### 3. Run the agent locally

```bash
export SSL_CERT_FILE=$(python -m certifi)
adk web
```

This launches the ADK dev UI at http://localhost:8000.

### 4. Test the agent

1. Open http://localhost:8000 in Chrome
2. Select **aza_agent** from the dropdown in the upper right
3. Click the **microphone button** (voice only — text input does not work with native audio models)
4. Say **"Hello?"** and wait for Aza to respond

**What to expect:** Aza picks up thinking you might be Cam. She reacts to whoever you are, then recruits you to go through a phone directory with her. She gives you numbers 104, 105, and 106 to start.

### 5. Test a returning caller

1. Stop the agent (Ctrl+C)
2. Restart with `adk web`
3. Click the microphone
4. Say **"Hey, I called those numbers you told me about"**

**What to expect:** Aza should skip the intro and ask which numbers you listened to, then respond to what you tell her and give you the next set.

### 6. Test the Cam claim

1. When Aza asks who you are, say **"I'm Cam"**

**What to expect:** She does not believe you. She says something like "even if you are Cam, that doesn't change what I need" and redirects you into the experience like any other caller.

## Run with FastAPI Server (production mode)

```bash
cd app
python main.py
```

Starts at http://localhost:8080. WebSocket endpoint at `/ws/{caller_id}`. This is the same server that runs on Cloud Run. It requires a frontend to test voice — the ADK dev UI (above) is easier for local testing.

## Deploy to Google Cloud Run

### Using the deploy script (recommended)

```bash
cd adk-streaming
chmod +x deploy.sh
./deploy.sh your_project_id your_api_key
```

This enables all required GCP APIs, sets IAM permissions, creates a Firestore database, and deploys to Cloud Run in one command.

### Manual deploy

```bash
cd adk-streaming
gcloud run deploy yhtbt-phone-booth --source . --region us-east1 --allow-unauthenticated --set-env-vars "GOOGLE_API_KEY=your_key,GOOGLE_GENAI_USE_VERTEXAI=FALSE" --memory 1Gi --timeout 300 --session-affinity
```

## The Agent

### Who She Is
Aza Fre, 22, works at Excursion Club in Nearstalgia Bay. She found Cam's travel videos online, got fascinated by the journey, and started digging through a phone directory Cam left behind. She has not found Cam. She is still looking. She thinks two people listening to the directory might catch something one person missed.

### What She Does
- Answers expecting someone else, reacts when she gets a stranger
- Recruits the caller to go through the directory with her
- Responds to their interpretation of what they heard — no wrong answers
- Moves them through 11 narrative cycles with branching paths
- Starts asking about the caller's own life as the conversation deepens
- Remembers things the caller said earlier and brings them back when relevant
- At the end, reveals she found Cam and invites the caller to Nearstalgia Bay (number 757)

### What She Won't Do
- Confirm there's a game
- Break character
- Give numbers without real engagement first
- Say where she's from
- Reveal where Cam is (until the very end)
- Sound like an assistant
- Correct the caller's interpretation — every answer is valid

### The Story Structure
11 cycles tracing Cam's journey from leaving home to coming back changed. Two branching points (Cycles 2 and 5) where the caller's interpretation determines which path they take. Personal questions about the caller's own life woven in starting around Cycle 3. The reveal at the end is earned — it only happens after the full journey.

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
- **Innovation & Multimodal UX (40%):** Fully realized character with distinct persona, 11-cycle branching narrative, personal questions about the caller's life, persistent session memory, lives inside an existing ARG campaign with an active audience
- **Technical Implementation (30%):** ADK with Gemini Live API, Firestore session tracking, Cloud Run deployment with automated deploy script, WebSocket bidirectional audio streaming
- **Demo & Presentation (30%):** Live demo through actual phone directory site, real conversation with barge-in support, architecture diagram included

## Credits

**Narrative Design:** Surf Noir Studio
**Album:** *You Had to Be There* by Cam Murdoch
**Campaign:** [youhadtobethere.life](https://youhadtobethere.life)
**Agent Framework:** [Google Agent Development Kit](https://google.github.io/adk-docs/)

---

*Surf Noir Studio · 2026*

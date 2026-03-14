"""YHTBT Phone Booth — FastAPI server with ADK streaming and Firestore session tracking."""

import os
import json
import asyncio
import base64
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables BEFORE importing the agent
load_dotenv()

from google.genai import types
from google.genai.types import Part, Content, Blob
from google.adk.runners import Runner
from google.adk.agents import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.sessions.in_memory_session_service import InMemorySessionService

from fastapi import FastAPI, WebSocket, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.websockets import WebSocketDisconnect

from aza_agent.agent import root_agent
from caller_store import get_or_create_caller, mark_returning, log_event, format_session_context

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- App Initialization ---
app = FastAPI(title="YHTBT Phone Booth")
session_service = InMemorySessionService()
runner = Runner(
    app_name="yhtbt-phone-booth",
    agent=root_agent,
    session_service=session_service,
)

# Serve static files (the phone UI)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Serve the phone booth UI."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"status": "YHTBT Phone Booth is running", "websocket": "/ws/{caller_id}"}


@app.websocket("/ws/{caller_id}")
async def websocket_endpoint(websocket: WebSocket, caller_id: str):
    """Handle a phone call via WebSocket with Firestore session tracking."""
    await websocket.accept()
    logger.info(f"Call connected: {caller_id}")

    # --- Firestore: Get caller history ---
    try:
        caller_data = get_or_create_caller(caller_id)
        session_context = format_session_context(caller_data)

        # Log the call event
        if caller_data.get("returning_caller") or caller_data.get("cycles_completed"):
            mark_returning(caller_id)
            log_event(caller_id, "aza_call_returned")
        else:
            log_event(caller_id, "aza_call_started")

        logger.info(f"Caller {caller_id}: {session_context[:100]}...")
    except Exception as e:
        logger.warning(f"Firestore error for {caller_id}, proceeding without history: {e}")
        session_context = "This is a new caller. They have not spoken to you before. Begin with the opening sequence."

    # --- ADK Session Setup ---
    session = await session_service.create_session(
        app_name="yhtbt-phone-booth",
        user_id=caller_id,
        state={"session_context": session_context},
    )

    # Inject session context as initial message so Aza knows caller history
    if session_context:
        initial_context = Content(
            role="user",
            parts=[Part(text=f"[SYSTEM CONTEXT - DO NOT READ ALOUD]: {session_context}")]
        )

    # --- Configure for native audio ---
    model_name = root_agent.model if isinstance(root_agent.model, str) else ""
    is_native_audio = "native-audio" in model_name.lower() if model_name else False

    run_config = RunConfig(
        response_modalities=["AUDIO"],
        streaming_mode=StreamingMode.BIDI,
        output_audio_transcription=types.AudioTranscriptionConfig(),
        input_audio_transcription=types.AudioTranscriptionConfig(),
    )

    # --- Start streaming ---
    live_request_queue = LiveRequestQueue()

    # Send session context as first message
    if session_context:
        live_request_queue.send_content(initial_context)

    live_events = runner.run_live(
        user_id=caller_id,
        session_id=session.id,
        live_request_queue=live_request_queue,
        run_config=run_config,
    )

    async def upstream_task():
        """Receive from WebSocket, forward to ADK."""
        try:
            while True:
                try:
                    # Try to receive binary audio first
                    data = await websocket.receive()

                    if "bytes" in data:
                        # Binary audio data
                        audio_data = data["bytes"]
                        live_request_queue.send_realtime(
                            Blob(data=audio_data, mime_type="audio/pcm;rate=16000")
                        )
                    elif "text" in data:
                        # JSON message (text or base64 audio)
                        msg = json.loads(data["text"])

                        if msg.get("type") == "audio" and msg.get("data"):
                            # Base64-encoded audio
                            audio_bytes = base64.b64decode(msg["data"])
                            live_request_queue.send_realtime(
                                Blob(data=audio_bytes, mime_type="audio/pcm;rate=16000")
                            )
                        elif msg.get("type") == "text" and msg.get("text"):
                            # Text message
                            live_request_queue.send_content(
                                Content(
                                    role="user",
                                    parts=[Part(text=msg["text"])]
                                )
                            )
                        elif msg.get("type") == "end":
                            logger.info(f"Caller {caller_id} hung up")
                            break
                except WebSocketDisconnect:
                    logger.info(f"Caller {caller_id} disconnected")
                    break
        except Exception as e:
            logger.error(f"Upstream error for {caller_id}: {e}")
        finally:
            live_request_queue.close()

    async def downstream_task():
        """Receive from ADK, forward to WebSocket."""
        try:
            async for event in live_events:
                event_json = event.model_dump_json(exclude_none=True, by_alias=True)
                try:
                    await websocket.send_text(event_json)
                except Exception:
                    break
        except Exception as e:
            logger.error(f"Downstream error for {caller_id}: {e}")

    # Run both tasks concurrently
    try:
        await asyncio.gather(upstream_task(), downstream_task())
    except Exception as e:
        logger.error(f"Session error for {caller_id}: {e}")
    finally:
        logger.info(f"Call ended: {caller_id}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
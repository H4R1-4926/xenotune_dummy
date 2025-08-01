from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse
from typing import Optional
from music_gen import generate_and_upload_loop, generate_music
from firebase import upload_to_firebase
import threading
import time
import os

app = FastAPI()

VALID_MODES = {"focus", "relax", "sleep"}
VALID_ACTIONS = {"play_loop", "generate_and_upload"}

# Shared state for the music loop
music_state = {
    "mode": "focus",
    "user_id": "",
}
stop_flag = {"value": False}
is_paused_flag = {"value": False}
pause_condition = threading.Condition()


# Background music loop
def start_music_loop(mode, user_id, initial_file=None):
    stop_flag["value"] = False
    is_paused_flag["value"] = False
    music_state["mode"] = mode
    music_state["user_id"] = user_id
    music_state["initial_file"] = initial_file
    thread = threading.Thread(
        target=generate_and_upload_loop,
        args=(music_state, stop_flag, pause_condition, is_paused_flag),
        daemon=True
    )
    thread.start()


@app.get("/music/{mode}")
async def music_mode_get(
    mode: str,
    user_id: Optional[str] = Query(None),
    action: str = Query("play_loop")
):
    if mode not in VALID_MODES:
        return JSONResponse({"error": "Invalid mode. Choose from focus, relax, or sleep."}, status_code=400)

    if action not in VALID_ACTIONS:
        return JSONResponse({"error": "Invalid action. Choose from play_loop or generate_and_upload."}, status_code=400)

    if action == "play_loop":
        start_music_loop(mode, user_id or "")
        return JSONResponse({"status": f"{mode.capitalize()} music loop started."})

    if action == "generate_and_upload":
        if not user_id:
            return JSONResponse({"error": "user_id is required for uploading."}, status_code=400)

        filename = f"{mode}_{int(time.time())}.mp3"
        local_path = generate_music(mode)

        if not local_path:
            return JSONResponse({"error": "Music generation failed."}, status_code=500)

        try:
            firebase_path = f"users/{user_id}/{filename}"
            url = upload_to_firebase(local_path, firebase_path)
            return JSONResponse({'download_url': url})
        except Exception as e:
            return JSONResponse({"error": f"Upload failed: {str(e)}"}, status_code=500)


@app.post("/generate-music")
async def generate_music_api(request: Request):
    try:
        try:
            data = await request.json()
        except Exception:
            return JSONResponse({"error": "Invalid JSON in request body."}, status_code=400)

        user_id = data.get("user_id")
        mode = data.get("mode", "sleep")

        if not user_id:
            return JSONResponse({"error": "user_id is required."}, status_code=400)

        # Generate M1 but do NOT upload here
        slot = "M1"
        filename = f"{slot}.mp3"
        firebase_path = f"users/{user_id}/{slot}.mp3"
        local_path = generate_music(mode)

        if not local_path or not os.path.exists(local_path):
            return JSONResponse({"error": "Music generation failed."}, status_code=500)

        download_url = upload_to_firebase(local_path, firebase_path)

        # Instead of uploading M1 here, pass the path to the loop function
        start_music_loop(mode, user_id, initial_file=local_path)

        return JSONResponse({
            'download_url': download_url,
            'status': f"{mode} generation started with alternating upload (M1/M2).",
            'filename': filename
        })

    except Exception as e:
        return JSONResponse({"error": f"Server error: {str(e)}"}, status_code=500)


@app.post("/pause")
def pause_generation():
    is_paused_flag["value"] = True
    with pause_condition:
        pause_condition.notify_all()
    return {"status": "paused"}

@app.post("/resume")
def resume_generation():
    is_paused_flag["value"] = False
    with pause_condition:
        pause_condition.notify_all()
    return {"status": "resumed"}

@app.post("/stop")
def stop_generation():
    stop_flag["value"] = True
    with pause_condition:
        pause_condition.notify_all()
    return {"status": "stopped"}
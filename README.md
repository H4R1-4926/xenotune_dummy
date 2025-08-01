# 🎶 Xenotune AI Music Generator

This project is the backend for the **Xenotune AI Music Generator**, an intelligent ambient music creation tool using Python’s `music21` library. It supports mood-based music generation: **Focus**, **Relax**, and **Sleep**. Built using FastAPI, it is lightweight, scalable, and integrates easily with a Flutter frontend.

---

## 📂 Project Structure

```
backend/
├── main.py            # FastAPI app and routes
├── music_gen.py       # Core music generation logic using music21
├── config.json        # Configuration for modes and instruments
├── output/            # Folder for generated MIDI files
```

---

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/xenotune-backend.git
cd xenotune-backend
```

### 2. Create and Activate Virtual Environment

```bash
python -m venv venv

# Activate the environment:
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

> Make sure `ffmpeg` is installed if you plan to use `.wav` ambient sounds with `pydub`.

---

## 🚀 Run the FastAPI Server

```bash
uvicorn main:app --reload
```
---

## 📡 API Endpoint

### `POST /generate/`

Generate a MIDI file based on the selected mood.

**Request (form-data):**
- `mode`: one of `focus`, `relax`, or `sleep`

**Response:**
- MIDI file (`.mid`) for download

---

## 🧾 Example cURL Request

```bash
curl -X POST "http://127.0.0.1:8000/generate/" -F "mode=relax" --output relax_output.mid
```

---

## 📦 Dependencies

- fastapi
- uvicorn
- music21
- pydub
- python-multipart

See `requirements.txt` for exact versions.

---

## 📌 License

This project is licensed under the MIT License. You are free to use, modify, and distribute.

---

## ✨ Credits

Developed with ❤️ by Sanjay & Abi 
Powered by FastAPI & music21

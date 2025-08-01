import os, time, json, shutil, random, subprocess, atexit, threading
from music21 import stream, chord, note, instrument, tempo, metadata, midi
from json_gen import main
from firebase import upload_to_firebase
from pathlib import Path

CONFIG_PATH = "config.json"
OUTPUT_PATH = "output"
FFMPEG_PATH = "ffmpeg"
ffprobe_path = "ffprobe"

SECTION_LENGTHS = {
    "intro": 4, "groove": 8, "verse": 8, "chorus": 8, "bridge": 8,
    "drop": 8, "build": 8, "solo": 8, "outro": 4, "loop": 16,
    "variation": 8, "layered_loop": 8, "fadeout": 4, "layer1": 8,
    "layer2": 8, "ambient_loop": 16, "dream_flow": 8, "infinite_loop": 16,
    "loop_a": 8, "focus_block": 8, "pause_fill": 4, "soothing_loop": 16,
    "deep_layer": 8, "dream_pad": 8
}

INSTRUMENT_MAP = {
    "Charango": instrument.Mandolin(), "Reeds": instrument.EnglishHorn(),
    "Harp": instrument.Harp(), "Piano": instrument.Piano(),
    "Electric Piano": instrument.ElectricPiano(), "Synth Lead": instrument.SopranoSaxophone(),
    "Bass Guitar": instrument.ElectricBass(), "Drum Kit": instrument.Woodblock(),
    "Arpeggiator": instrument.Harpsichord(), "Acoustic Guitar": instrument.AcousticGuitar(),
    "Soft Strings": instrument.Violin(), "Felt Piano": instrument.Piano(),
    "Air Pad": instrument.ElectricOrgan(), "Sub Bass": instrument.Contrabass(),
    "Flute": instrument.Flute(), "Chill Guitar": instrument.AcousticGuitar(),
    "Electric Guitar": instrument.ElectricGuitar()
}

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def get_music21_instrument(name):
    return INSTRUMENT_MAP.get(name, instrument.Instrument(name))

def convert_midi_to_mp3(midi_path):
    bgm_path = "assets/bgm.mp3"
    mp3_path = midi_path.replace(".mid", ".mp3")
    final_mix = midi_path.replace(".mid", "_mixed.mp3")

    # Convert MIDI to audio using soundfont or plugin (assumed external setup already done)
    subprocess.run([
        FFMPEG_PATH, "-y", "-i", midi_path, mp3_path
    ], check=True)

    # Mix with background music
    subprocess.run([
        FFMPEG_PATH, "-y",
        "-i", mp3_path,
        "-i", bgm_path,
        "-filter_complex", "[0:a]volume=1.0[a0];[1:a]volume=0.3[a1];[a0][a1]amix=inputs=2:duration=first",
        "-c:a", "libmp3lame", final_mix
    ], check=True)

    if os.path.exists(mp3_path):
        os.remove(mp3_path)
    return final_mix

def create_melody_part(mode, structure, progression):
    melody_part = stream.Part()
    melody_part.insert(0, {"focus": instrument.ElectricPiano(), "relax": instrument.Piano(), "sleep": instrument.Piano()}.get(mode, instrument.Piano()))
    scale_map = {
        "focus": ["C5", "D5", "E5", "F5", "G5", "A5"],
        "relax": ["C4", "D4", "E4", "G4", "A4"],
        "sleep": ["A3", "B3", "C4", "D4", "E4"]
    }
    melody_notes = scale_map.get(mode, ["C4", "D4", "E4", "G4"])

    for section_name in structure:
        beats, section_beats = 0, SECTION_LENGTHS.get(section_name, 8) * 4
        motif = [random.choice(melody_notes) for _ in range(4)]
        while beats < section_beats:
            phrase = random.choice([motif, motif[::-1], [random.choice(melody_notes) for _ in range(4)]])
            for pitch in phrase:
                dur = random.choice([0.5, 1.0, 1.5]) if mode == "focus" else 1.0
                n = note.Note(pitch, quarterLength=dur)
                n.volume.velocity = random.randint(40, 70)
                melody_part.append(n)
                beats += dur
                if beats >= section_beats:
                    break
    return melody_part

def generate_music(mode):
    try:
        config = load_config()
        mode_data = config.get(mode)
        if not mode_data:
            raise ValueError(f"Invalid mode '{mode}' in config.")

        bpm = mode_data.get("tempo", 80)
        instruments = mode_data.get("instruments", [])
        structure = mode_data.get("structure", ["intro", "loop", "outro"])

        shutil.rmtree(OUTPUT_PATH, ignore_errors=True)
        os.makedirs(OUTPUT_PATH, exist_ok=True)

        score = stream.Score()
        fluctuated_bpm = bpm + random.choice([-2, 0, 1])
        score.append(tempo.MetronomeMark(number=fluctuated_bpm))
        score.insert(0, metadata.Metadata(title=f"Xenotune - {mode.title()} Mode"))

        chord_sets = {
            "focus": [["C4", "E4", "G4"], ["D4", "F4", "A4"], ["G3", "B3", "D4"]],
            "relax": [["C4", "G4", "A4"], ["E4", "G4", "B4"], ["D4", "F4", "A4"]],
            "sleep": [["C3", "E3", "G3"], ["A3", "C4", "E4"], ["F3", "A3", "C4"]]
        }
        progression = chord_sets.get(mode, [["C4", "E4", "G4"]])

        for inst in instruments:
            if "samples" in inst:
                continue
            part = stream.Part()
            part.insert(0, get_music21_instrument(inst.get("name", "Piano")))
            style = inst.get("style", "")
            notes = inst.get("notes", random.choice(progression))

            for section_name in structure:
                beats, section_beats = 0, SECTION_LENGTHS.get(section_name, 8) * 4
                velocity_range = (20, 50) if "ambient" in style else (30, 70)
                while beats < section_beats:
                    vel = random.randint(*velocity_range)
                    if "slow" in style or "ambient" in style:
                        c = chord.Chord(random.choice(progression), quarterLength=1.5)
                    elif "arp" in style:
                        for n in notes:
                            nt = note.Note(n, quarterLength=0.5)
                            nt.volume.velocity = vel
                            part.append(nt)
                            beats += 0.5
                            if beats >= section_beats:
                                break
                        continue
                    else:
                        c = chord.Chord(random.choice(progression), quarterLength=1.0)
                    c.volume.velocity = vel
                    part.append(c)
                    beats += c.quarterLength
            score.append(part)

        melody_part = create_melody_part(mode, structure, progression)
        score.append(melody_part)

        midi_path = f"{mode}.mid"
        mf = midi.translate.streamToMidiFile(score)
        mf.open(midi_path, 'wb'); mf.write(); mf.close()

        return convert_midi_to_mp3(midi_path)

    except Exception as e:
        print(f"⚠️ Error generating music: {e}")
        return None

def get_audio_duration(file_path):
    """Returns the duration (in seconds) of the given audio file using ffprobe."""
    try:
        result = subprocess.run(
            [
                ffprobe_path, "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                file_path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,

            text=True
        )
        return float(result.stdout.strip())
    except Exception as e:
        print(f"⚠️ Failed to get duration of {file_path}: {e}")
        return 0

def wait_with_pause(duration, stop_flag, pause_condition, is_paused_flag):
    """Wait for duration seconds but support pause/resume."""
    waited = 0
    interval = 0.5  # check every 0.5s
    while waited < duration:
        with pause_condition:
            if stop_flag["value"]:
                break
            while is_paused_flag["value"]:
                print("⏸️ Paused during wait...")
                pause_condition.wait()

        time.sleep(interval)
        waited += interval


def generate_and_upload_loop(music_state, stop_flag, pause_condition, is_paused_flag):
    print("🔁 Music generation/upload loop started...")

    try:
        current_mode = music_state.get("mode", "focus")
        current_user = music_state.get("user_id")

        current_slot = "M1"
        next_slot = "M2"

        current_mp3 = music_state.get("initial_file")
        if not current_mp3 or not os.path.exists(current_mp3):
            print("❌ Initial music file missing.")
            return

        # Upload M1
        upload_to_firebase(current_mp3, f"users/{current_user}/{current_slot}.mp3")
        print(f"☁️ Uploaded {current_slot}.mp3")

        

        while not stop_flag["value"]:
            # 🔄 Start generating M2 in background
            result_holder = {"file": None}

            def generate_next():
                result_holder["file"] = generate_music(current_mode)

            gen_thread = threading.Thread(target=generate_next, daemon=True)
            gen_thread.start()

            # ⏯️ While generating M2, play current file
            duration = get_audio_duration(current_mp3)
            print(f"🎵 Playing {current_slot}.mp3 | ⏱️ {duration:.1f}s")

            # 🔁 Start playback in a thread so we can continue
            def playback_sim():
                wait_with_pause(duration, stop_flag, pause_condition, is_paused_flag)

            play_thread = threading.Thread(target=playback_sim, daemon=True)
            play_thread.start()

            # ✅ Wait for M2 to finish generating
            gen_thread.join()
            next_gen_file = result_holder["file"]

            if not next_gen_file or not os.path.exists(next_gen_file):
                print("⚠️ Generation failed. Stopping.")
                break

            # ✅ Upload M2 immediately after generation
            upload_to_firebase(next_gen_file, f"users/{current_user}/{next_slot}.mp3")
            print(f"☁️ Uploaded: {next_slot}.mp3")

            # 🔄 Wait for current to finish playing (if not done yet)
            play_thread.join()

            # 🔁 Rotate
            current_mp3 = next_gen_file
            current_slot, next_slot = next_slot, current_slot

    finally:
        print("🛑 Music loop stopped.")






def cleanup():
    global stop_thread
    stop_thread = True
    print("🧹 Cleanup triggered. Music loop will stop.")

atexit.register(cleanup)
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from TTS.api import TTS
from pydub import AudioSegment
import os, uuid

app = FastAPI(title="TTS API", description="Coqui XTTS - Text to Speech API")

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

os.makedirs("tts_outputs", exist_ok=True)

male_speakers   = ["Luis Moray", "Andrew Chipper"]
female_speakers = ["Daisy Studious", "Gracie Wise"]

SUPPORTED_LANGUAGES = ["ar", "en", "fr", "es", "de", "it", "tr", "ru", "hi"]


class TTSRequest(BaseModel):
    text: str
    language: str = "en"   # ar, en, fr, es, de, it, tr, ru, hi
    gender: str   = "female"  # male or female
    speaker_index: int = 0    # 0 or 1


def split_text(text, max_length=160):
    sentences = []
    while len(text) > max_length:
        split_index = text.rfind(" ", 0, max_length)
        if split_index == -1:
            split_index = max_length
        sentences.append(text[:split_index].strip())
        text = text[split_index:].strip()
    if text:
        sentences.append(text)
    return sentences

# ---------- Endpoints ----------
@app.get("/")
def root():
    return {"message": "TTS API is running ✅"}

@app.post("/tts")
def synthesize(req: TTSRequest):
    # Validate
    if not req.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")
    if req.language not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language. Choose from: {SUPPORTED_LANGUAGES}")
    if req.gender not in ["male", "female"]:
        raise HTTPException(status_code=400, detail="Gender must be 'male' or 'female'.")


    speakers = male_speakers if req.gender == "male" else female_speakers
    idx = req.speaker_index % len(speakers)
    speaker = speakers[idx]

    # Output file
    output_path = os.path.join("tts_outputs", f"{uuid.uuid4()}.wav")
    parts = split_text(req.text)
    temp_files = []

    try:
        for i, part in enumerate(parts, start=1):
            temp_file = os.path.join("tts_outputs", f"temp_{uuid.uuid4()}.wav")
            tts.tts_to_file(
                text=part,
                speaker=speaker,
                language=req.language,
                file_path=temp_file
            )
            temp_files.append(temp_file)


        combined = None
        for f in temp_files:
            seg = AudioSegment.from_wav(f)
            combined = seg if combined is None else combined + seg

        combined.export(output_path, format="wav")

    finally:
        for f in temp_files:
            if os.path.exists(f):
                os.remove(f)


    return FileResponse(
        path=output_path,
        media_type="audio/wav",
        filename="output.wav",
        headers={"X-Speaker": speaker}
    )

@app.get("/speakers")
def get_speakers():
    return {
        "male": male_speakers,
        "female": female_speakers,
        "languages": SUPPORTED_LANGUAGES
    }
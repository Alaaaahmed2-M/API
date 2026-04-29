from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from TTS.api import TTS
from pydub import AudioSegment

app = FastAPI()

os.makedirs("tts_outputs", exist_ok=True)

tts = TTS(
    model_name="tts_models/multilingual/multi-dataset/xtts_v2",
    progress_bar=False,
    gpu=False
)

available_speakers = tts.speakers

male_candidates = ["Craig Gutsy"]
female_candidates = ["Gracie Wise"]

male_speakers = [s for s in male_candidates if s in available_speakers] or [available_speakers[0]]
female_speakers = [s for s in female_candidates if s in available_speakers] or [available_speakers[0]]

speaker_indices = {"male": 0, "female": 0}


class TTSRequest(BaseModel):
    text: str
    language: str
    gender: str


def get_next_speaker(gender):
    speakers = male_speakers if gender == "male" else female_speakers
    index = speaker_indices[gender]
    speaker = speakers[index]
    speaker_indices[gender] = (index + 1) % len(speakers)
    return speaker


def split_text(text, max_length=400, min_words=100):
    words = text.split()

    if len(words) <= min_words:
        return [text]

    parts = []
    current = []

    for word in words:
        current.append(word)
        current_text = " ".join(current)

        if len(current) >= min_words and len(current_text) >= max_length:
            parts.append(current_text)
            current = []

    if current:
        parts.append(" ".join(current))

    return parts


def get_next_filename():
    i = 1
    while True:
        path = os.path.join("tts_outputs", f"output_{i}.wav")
        if not os.path.exists(path):
            return path
        i += 1


@app.post("/tts")
def generate_tts(req: TTSRequest):
    speaker = get_next_speaker(req.gender)
    output_path = get_next_filename()

    parts = split_text(req.text)

    combined_audio = AudioSegment.empty()
    temp_files = []

    for i, part in enumerate(parts, start=1):
        temp_file = f"tts_outputs/temp_{i}.wav"

        tts.tts_to_file(
            text=part,
            speaker=speaker,
            language=req.language,
            file_path=temp_file
        )

        temp_files.append(temp_file)

    for file in temp_files:
        combined_audio += AudioSegment.from_wav(file)

    combined_audio.export(output_path, format="wav")

    for file in temp_files:
        try:
            os.remove(file)
        except Exception:
            pass

    return FileResponse(
        path=output_path,
        media_type="audio/wav",
        filename=os.path.basename(output_path)
    )

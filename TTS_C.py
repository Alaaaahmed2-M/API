import tkinter as tk
from tkinter import messagebox
import threading
from playsound3 import playsound
import os
from TTS.api import TTS
from pydub import AudioSegment

os.makedirs("tts_outputs", exist_ok=True)

tts = TTS(model_name="tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=False, gpu=False)

male_speakers = ["Craig Gutsy"]
female_speakers = ["Gracie Wise"]

speaker_indices = {"male": 0, "female": 0}

def get_next_speaker(gender):
    index = speaker_indices[gender]
    speakers = male_speakers if gender == "male" else female_speakers
    speaker = speakers[index]
    speaker_indices[gender] = (index + 1) % len(speakers)
    return speaker

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

def convert_text_to_speech():
    text = text_input.get("1.0", tk.END).strip()
    if not text:
        messagebox.showwarning("Warning", "Please enter some text first!")
        return

    lang = lang_var.get()
    if not lang:
        messagebox.showwarning("Warning", "Please select a language!")
        return

    gender = gender_var.get()
    if not gender:
        messagebox.showwarning("Warning", "Please select gender (Male/Female)!")
        return

    try:
        speaker = get_next_speaker(gender)
        output_path = os.path.join("tts_outputs", f"{speaker.replace(' ', '_')}.wav")
        parts = split_text(text)
        if len(parts) > 1:
            messagebox.showinfo("Info", f"Text is long. It will be split into {len(parts)} parts.")

        combined_audio = None
        temp_files = []

        for i, part in enumerate(parts, start=1):
            temp_file = os.path.join("tts_outputs", f"temp_part_{i}.wav")
            tts.tts_to_file(
                text=part,
                speaker=speaker,
                language=lang,
                file_path=temp_file
            )
            temp_files.append(temp_file)

        for i, f in enumerate(temp_files):
            segment = AudioSegment.from_wav(f)
            if combined_audio is None:
                combined_audio = segment
            else:
                combined_audio += segment

        combined_audio.export(output_path, format="wav")

        playsound(output_path)
        for f in temp_files:
            os.remove(f)

        messagebox.showinfo("Done", f"Speech generated successfully using: {speaker}")

    except Exception as e:
        messagebox.showerror("Error", str(e))

def start_conversion():
    threading.Thread(target=convert_text_to_speech).start()

root = tk.Tk()
root.title("Coqui XTTS - Realistic Voice Generator")
root.geometry("620x550")
root.resizable(False, False)
root.configure(bg="#f2f4f7")

title_label = tk.Label(
    root,
    text="Text-to-Speech Converter",
    font=("Arial", 18, "bold"),
    fg="#2E7D32",
    bg="#f2f4f7"
)
title_label.pack(pady=15)

tk.Label(root, text="Enter your text below:", font=("Arial", 12, "bold"), bg="#f2f4f7").pack(pady=5)
text_input = tk.Text(root, height=10, width=70, font=("Arial", 11), relief="solid", bd=1)
text_input.pack(pady=10)

def paste_text(event=None):
    try:
        text_input.insert(tk.INSERT, root.clipboard_get())
    except tk.TclError:
        pass

text_input.bind("<Control-v>", paste_text)
text_input.bind("<Control-V>", paste_text)
text_input.bind("<Button-3>", lambda e: paste_text())

tk.Label(root, text="Select Language:", font=("Arial", 12, "bold"), bg="#f2f4f7").pack(pady=5)
lang_var = tk.StringVar(value="en")
lang_menu = tk.OptionMenu(root, lang_var, "ar", "en", "fr", "es", "de", "it", "tr", "ru", "hi")
lang_menu.config(font=("Arial", 11), width=12, bg="#ffffff")
lang_menu.pack(pady=5)

tk.Label(root, text="Select Gender (for English voices):", font=("Arial", 12, "bold"), bg="#f2f4f7").pack(pady=5)
gender_var = tk.StringVar()
gender_menu = tk.OptionMenu(root, gender_var, "male", "female")
gender_menu.config(font=("Arial", 11), width=12, bg="#ffffff")
gender_menu.pack(pady=5)

convert_button = tk.Button(
    root,
    text="Convert Text to Speech",
    command=start_conversion,
    font=("Arial", 13, "bold"),
    bg="#4CAF50",
    fg="white",
    padx=20,
    pady=10,
    relief="raised",
    cursor="hand2"
)
convert_button.pack(pady=25)

footer = tk.Label(
    root,
    text="Powered by Coqui XTTS | Multilingual Realistic Voices",
    font=("Arial", 9, "italic"),
    fg="#555",
    bg="#f2f4f7"
)
footer.pack(pady=10)

root.mainloop()

def generate_tts_api(text, lang, gender):
    # -------- Validation --------
    if not text or not text.strip():
        raise ValueError("Text cannot be empty")

    gender = gender.lower()
    if gender not in ["male", "female"]:
        raise ValueError("Gender must be 'male' or 'female'")

    supported_languages = ["ar", "en", "fr", "es", "de", "it", "tr", "ru", "hi"]
    if lang not in supported_languages:
        raise ValueError(f"Language must be one of {supported_languages}")
    # ----------------------------

    speaker = get_next_speaker(gender)
    output_path = os.path.join("tts_outputs", f"{speaker.replace(' ', '_')}.wav")

    parts = split_text(text)
    temp_files = []

    for i, part in enumerate(parts, start=1):
        temp_file = os.path.join("tts_outputs", f"temp_part_{i}.wav")
        tts.tts_to_file(
            text=part,
            speaker=speaker,
            language=lang,
            file_path=temp_file
        )
        temp_files.append(temp_file)

    combined_audio = None
    for f in temp_files:
        segment = AudioSegment.from_wav(f)
        combined_audio = segment if combined_audio is None else combined_audio + segment

    combined_audio.export(output_path, format="wav")

    for f in temp_files:
        os.remove(f)

    return output_path


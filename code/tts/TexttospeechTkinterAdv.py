import edge_tts
import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext
import pandas as pd
import re
import os

try:
    import nest_asyncio
    nest_asyncio.apply()
except ImportError:
    pass

async def get_voices_df():
    voices = await edge_tts.list_voices()
    df = pd.DataFrame(voices)
    return df

voices_df = asyncio.run(get_voices_df())

voices_df['FriendlyName'] = voices_df['FriendlyName'].apply(
    lambda x: re.sub(r'Microsoft|Online|Natural|(|)|\(\)', '', x).strip()
)

def get_available_voices(gender):
    voices_list = (
        voices_df[voices_df['Gender'] == gender][['ShortName', 'FriendlyName']]
        .loc[lambda x: x['FriendlyName'].str.contains(r'English', regex=True)]
        .assign(FriendlyName=lambda x: x['FriendlyName'].str.replace(r'\s*\(\)', '', regex=True))
        .apply(tuple, axis=1)
        .tolist()
    )
    return voices_list

async def text_to_speech(text, filename="output.mp3", voice="en-US-GuyNeural", rate="+0%", pitch="+0Hz"):
    text = re.sub(r"[*/#]", " ", text).replace("—", ". ")
    tts = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    audio_path = f"{filename}.mp3"
    await tts.save(audio_path)
    return text, audio_path

def convert_text_to_speech():
    text = text_area.get("1.0", tk.END).strip()
    filename = filename_entry.get()
    gender = gender_var.get()
    voice = voice_var.get()
    rate = f"{'+' if rate_slider.get() >= 0 else ''}{int(rate_slider.get())}%" #fix rate string
    pitch = f"{'+' if pitch_slider.get() >= 0 else ''}{int(pitch_slider.get())}Hz" #fix pitch string

    if not text or not filename:
        result_label.config(text="Please enter text and filename.", foreground="red")
        return

    available_voices = get_available_voices(gender)
    if not available_voices:
        result_label.config(text=f"No English voices found for {gender}.", foreground="red")
        return

    selected_voice = next((v[0] for v in available_voices if v[1] == voice), None)
    if not selected_voice:
        result_label.config(text="Please select a valid voice.", foreground="red")
        return

    full_filename = f"{filename}_{voice.replace(' ', '_')}_{rate.replace('%','')}_{pitch.replace('Hz','')}"

    try:
        refined_text, filepath = asyncio.run(text_to_speech(text, full_filename, selected_voice, rate, pitch))
        result_label.config(text=f"Audio file generated: {filepath}", foreground="green")
    except Exception as e:
        result_label.config(text=f"Error: {e}", foreground="red")

def update_voice_dropdown(*args):
    gender = gender_var.get()
    available_voices = get_available_voices(gender)
    voice_names = [v[1] for v in available_voices]
    voice_dropdown['values'] = voice_names
    if voice_names:
        voice_var.set(voice_names[0])
    else:
        voice_var.set("")

root = tk.Tk()
root.title("Text-to-Speech Converter")
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))

style = ttk.Style()
style.configure("TFrame", background="#f0f0f0", padding=10, borderwidth=2, relief="groove")
style.configure("TLabel", background="#f0f0f0", padding=5)
style.configure("TButton", padding=5)
style.configure("TEntry", padding=5)
style.configure("TCombobox", padding=5)
style.configure("TScale", padding=5)

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

text_label = ttk.Label(main_frame, text="Enter Text:")
text_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

text_area = scrolledtext.ScrolledText(main_frame, height=25, width=60)
text_area.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="we")

filename_label = ttk.Label(main_frame, text="Filename:")
filename_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

filename_entry = ttk.Entry(main_frame, width=60)
filename_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")

gender_label = ttk.Label(main_frame, text="Gender:")
gender_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)

gender_var = tk.StringVar()
gender_var.set("Male")
gender_var.trace("w", update_voice_dropdown)

gender_combobox = ttk.Combobox(main_frame, textvariable=gender_var, values=["Male", "Female"], state="readonly")
gender_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="we")

voice_label = ttk.Label(main_frame, text="Voice:")
voice_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)

voice_var = tk.StringVar()
voice_dropdown = ttk.Combobox(main_frame, textvariable=voice_var, state="readonly")
voice_dropdown.grid(row=4, column=1, padx=5, pady=5, sticky="we")

update_voice_dropdown()

rate_label = ttk.Label(main_frame, text="Rate:")
rate_label.grid(row=5, column=0, sticky="w", padx=5, pady=5)

rate_slider = tk.Scale(main_frame, from_=-100, to=100, orient=tk.HORIZONTAL)
rate_slider.set(0)
rate_slider.grid(row=5, column=1, padx=5, pady=5, sticky="we")

pitch_label = ttk.Label(main_frame, text="Pitch:")
pitch_label.grid(row=6, column=0, sticky="w", padx=5, pady=5)

pitch_slider = tk.Scale(main_frame, from_=-100, to=100, orient=tk.HORIZONTAL)
pitch_slider.set(0)
pitch_slider.grid(row=6, column=1, padx=5, pady=5, sticky="we")

convert_button = ttk.Button(main_frame, text="Convert to Speech", command=convert_text_to_speech)
convert_button.grid(row=7, column=0, columnspan=2, pady=10)

result_label = ttk.Label(main_frame, text="")
result_label.grid(row=8, column=0, columnspan=2, pady=5)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

root.mainloop()
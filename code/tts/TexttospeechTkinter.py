import edge_tts
import asyncio
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
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
    voice_index = voice_listbox.curselection()
    rate = rate_entry.get()
    pitch = pitch_entry.get()

    if not text or not filename:
        result_label.config(text="Please enter text and filename.", foreground="red")
        return

    available_voices = get_available_voices(gender)
    if not available_voices:
        result_label.config(text=f"No English voices found for {gender}.", foreground="red")
        return

    if not voice_index:
        result_label.config(text="Please select a voice.", foreground="red")
        return

    selected_voice = available_voices[voice_index[0]][0]
    selected_voice_name = available_voices[voice_index[0]][1].replace(" ", "_")

    if not rate:
        rate = "+0%"
    if not pitch:
        pitch = "+0Hz"

    full_filename = f"{filename}_{selected_voice_name}_{rate.replace('%','')}_{pitch.replace('Hz','')}"

    try:
        refined_text, filepath = asyncio.run(text_to_speech(text, full_filename, selected_voice, rate, pitch))
        result_label.config(text=f"Audio file generated: {filepath}", foreground="green")
    except Exception as e:
        result_label.config(text=f"Error: {e}", foreground="red")

def update_voice_list(*args):
    gender = gender_var.get()
    available_voices = get_available_voices(gender)

    voice_listbox.delete(0, tk.END)
    for i, friendly_name in enumerate(available_voices):
        voice_listbox.insert(tk.END, friendly_name[1])

def browse_save_location():
    filename = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")])
    if filename:
        filename_entry.delete(0, tk.END)
        filename_entry.insert(0, os.path.splitext(os.path.basename(filename))[0])

root = tk.Tk()
root.title("Text-to-Speech Converter")
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight())) #span whole screen.

style = ttk.Style()
style.configure("TFrame", background="#f0f0f0", padding=10, borderwidth=2, relief="groove")
style.configure("TLabel", background="#f0f0f0", padding=5)
style.configure("TButton", padding=5)
style.configure("TEntry", padding=5)
style.configure("TCombobox", padding=5)
style.configure("TListbox", padding=5)
style.configure("ScrolledText", padding=5)

main_frame = ttk.Frame(root)
main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

text_label = ttk.Label(main_frame, text="Enter Text:")
text_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)

text_area = scrolledtext.ScrolledText(main_frame, height=15, width=80)
text_area.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="we")

filename_label = ttk.Label(main_frame, text="Filename:")
filename_label.grid(row=2, column=0, sticky="w", padx=5, pady=5)

filename_entry = ttk.Entry(main_frame, width=60)
filename_entry.grid(row=2, column=1, padx=5, pady=5, sticky="we")

gender_label = ttk.Label(main_frame, text="Gender:")
gender_label.grid(row=3, column=0, sticky="w", padx=5, pady=5)

gender_var = tk.StringVar()
gender_var.set("Male")
gender_var.trace("w", update_voice_list)

gender_combobox = ttk.Combobox(main_frame, textvariable=gender_var, values=["Male", "Female"], state="readonly")
gender_combobox.grid(row=3, column=1, padx=5, pady=5, sticky="we")

voice_label = ttk.Label(main_frame, text="Voice:")
voice_label.grid(row=4, column=0, sticky="w", padx=5, pady=5)

voice_listbox = tk.Listbox(main_frame, height=8, width=60)
voice_listbox.grid(row=4, column=1, padx=5, pady=5, sticky="we")

update_voice_list()

rate_label = ttk.Label(main_frame, text="Rate:")
rate_label.grid(row=5, column=0, sticky="w", padx=5, pady=5)

rate_entry = ttk.Entry(main_frame, width=10)
rate_entry.insert(0, "+0%")
rate_entry.grid(row=5, column=1, sticky="w", padx=5, pady=5)

pitch_label = ttk.Label(main_frame, text="Pitch:")
pitch_label.grid(row=6, column=0, sticky="w", padx=5, pady=5)

pitch_entry = ttk.Entry(main_frame, width=10)
pitch_entry.insert(0, "+0Hz")
pitch_entry.grid(row=6, column=1, sticky="w", padx=5, pady=5)

convert_button = ttk.Button(main_frame, text="Convert to Speech", command=convert_text_to_speech)
convert_button.grid(row=7, column=0, columnspan=2, pady=10)

result_label = ttk.Label(main_frame, text="")
result_label.grid(row=8, column=0, columnspan=2, pady=5)

root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=1)

root.mainloop()
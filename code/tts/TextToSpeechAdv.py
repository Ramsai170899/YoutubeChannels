import edge_tts
import asyncio
import IPython.display as ipd
import nest_asyncio
import pandas as pd
import re

nest_asyncio.apply()

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
    return text, audio_path, ipd.Audio(audio_path, autoplay=True)

def main():
    text = input("\nEnter the text to convert to speech: ")
    filename = input("\nEnter filename (without .mp3): ") #get filename once

    while True:
        gender = input("\nEnter gender (Male/Female): ").capitalize()
        available_voices = get_available_voices(gender)

        if not available_voices:
            print(f"No English voices found for {gender}.")
            return

        print("Available voices:")
        for i, friendly_name in enumerate(available_voices):
            print(f"{i + 1}. {friendly_name[1]}")

        voice_index = int(input(f"\nSelect voice (1-{len(available_voices)}): ")) - 1
        selected_voice = available_voices[voice_index][0]
        selected_voice_name = available_voices[voice_index][1].replace(" ", "_")

        rate = input("\nEnter rate adjustment (e.g., +5%, -10%): ")
        if not rate:
            rate = "+0%"

        pitch = input("\nEnter pitch adjustment (e.g., +5Hz, -5Hz): ")
        if not pitch:
            pitch = "+0Hz"

        full_filename = f"{filename}_{selected_voice_name}_{rate.replace('%','')}_{pitch.replace('Hz','')}"

        refined_text, filepath, audio_output = asyncio.run(text_to_speech(text, full_filename, selected_voice, rate, pitch))

        print(f"Audio file generated: {filepath}")

        another_voice = input("\nTry another voice? (yes/no): ").lower()
        if another_voice != "yes":
            print("Ok then! See you soon !!!")
            break

if __name__ == "__main__":
    main()
# pip install edge-tts nest_asyncio


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

voices_list = (
    voices_df[voices_df['Gender'] == 'Female'][['ShortName', 'FriendlyName']]
    .loc[lambda x: x['FriendlyName'].str.contains(r'English', regex=True)]
    .assign(FriendlyName=lambda x: x['FriendlyName'].str.replace(r'\s*\(\)', '', regex=True))
    .apply(tuple, axis=1)
    .tolist()
)

text = """


Hi pyla. how are you ?


"""



person = "GuyNeural"
location = "US"
filename = """pyla"""


rate = "+5%"
pitch = "-5Hz"


async def text_to_speech(text, filename="output.mp3", voice=f"en-{location}-{person}", rate=rate, pitch=pitch):
    text = re.sub(r"[*/#]", " ", text).replace("—", ". ")
    tts = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    audio_path = f"{filename}_{person}_{rate}_{pitch}.mp3"
    await tts.save(audio_path)
    return text, audio_path, ipd.Audio(audio_path, autoplay=True)
refined_text, filename,audio_output = asyncio.run(text_to_speech(text, filename=filename))

print(f"Audio file is generated: {filename}")





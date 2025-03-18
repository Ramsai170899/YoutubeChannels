from flask import Flask, render_template, request, jsonify, send_from_directory
import edge_tts
import asyncio
import pandas as pd
import re
import os

app = Flask(__name__)
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

# Prepare voices dataframe


async def get_voices_df():
    voices = await edge_tts.list_voices()
    df = pd.DataFrame(voices)

    # Remove unwanted Microsoft, Online, Natural words
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'Microsoft|Online|Natural', '', x))

    # Remove only parentheses but KEEP the content inside
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: x.replace('(', '').replace(')', ''))

    # Remove hyphens, underscores
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'[-_]', '', x))

    # Remove extra spaces
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'\s+', ' ', x).strip())

    return df


voices_df = asyncio.run(get_voices_df())


def get_available_voices(gender):
    voices_list = (
        voices_df[voices_df['Gender'] == gender][['ShortName', 'FriendlyName']]
        .loc[lambda x: x['FriendlyName'].str.contains(r'English', regex=True)]
        .apply(tuple, axis=1)
        .tolist()
    )
    return voices_list


async def text_to_speech(text, filename="output", voice="en-US-GuyNeural", rate="+0%", pitch="+0Hz"):
    text = re.sub(r"[*/#]", " ", text).replace("—", ". ")
    tts = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    audio_path = os.path.join(output_folder, f"{filename}.mp3")
    await tts.save(audio_path)
    return audio_path


@app.route("/", methods=["GET", "POST"])
def index():
    genders = ["Male", "Female"]
    selected_gender = "Male"
    selected_voice_name = None
    generated_file = None
    voices = get_available_voices(selected_gender)

    if request.method == "POST":
        text = request.form.get("text")
        filename = request.form.get("filename")
        selected_gender = request.form.get("gender")
        selected_voice_name = request.form.get("voice")
        rate = request.form.get("rate")
        pitch = request.form.get("pitch")

        voices = get_available_voices(selected_gender)

        if text and filename:
            # Get both ShortName and FriendlyName
            selected_voice_tuple = next(
                (v for v in voices if v[1] == selected_voice_name), None)

            if selected_voice_tuple:
                selected_voice_shortname = selected_voice_tuple[0]

                rate_str = f"{'+' if int(rate) >= 0 else ''}{int(rate)}%"
                pitch_str = f"{'+' if int(pitch) >= 0 else ''}{int(pitch)}Hz"

                # Use ShortName in filename, replace hyphens with underscores
                clean_shortname = selected_voice_shortname.replace('-', '_')
                full_filename = f"{filename}_{clean_shortname}_{rate.replace('%','')}_{pitch.replace('Hz','')}"

                try:
                    asyncio.run(text_to_speech(text, full_filename,
                                selected_voice_shortname, rate_str, pitch_str))
                    generated_file = f"{full_filename}.mp3"
                except Exception:
                    pass  # Silently ignore errors

    return render_template("index.html",
                           genders=genders,
                           voices=voices,
                           selected_gender=selected_gender,
                           selected_voice_name=selected_voice_name,
                           generated_file=generated_file)


@app.route("/get_voices/<gender>")
def get_voices_api(gender):
    voices = get_available_voices(gender)
    voice_names = [v[1] for v in voices]
    return jsonify(voice_names)


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(output_folder, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

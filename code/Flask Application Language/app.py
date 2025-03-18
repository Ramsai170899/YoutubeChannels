from flask import Flask, render_template, request, jsonify, send_from_directory
import edge_tts
import asyncio
import pandas as pd
import re
import os
import pycountry  # Importing pycountry to convert language codes to full names

app = Flask(__name__)
output_folder = "output"
os.makedirs(output_folder, exist_ok=True)

# Function to retrieve and process voices


async def get_voices_df():
    voices = await edge_tts.list_voices()
    df = pd.DataFrame(voices)

    # Clean FriendlyName
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'Microsoft|Online|Natural', '', x))
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: x.replace('(', '').replace(')', ''))
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'[-_]', ' ', x))
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'\s+', ' ', x).strip())

    # Extract language codes and convert to full language names
    def get_language_name(locale):
        language_code = locale.split('-')[0]
        try:
            language = pycountry.languages.get(alpha_2=language_code)
            return language.name if language else 'Unknown'
        except AttributeError:
            return 'Unknown'

    df['Language'] = df['Locale'].apply(get_language_name)

    return df

# Initialize voices dataframe
voices_df = asyncio.run(get_voices_df())

# Retrieve unique language names for the dropdown
languages = voices_df['Language'].unique().tolist()

# Function to get available voices based on selected language and gender


def get_available_voices(selected_language, gender):
    voices_filtered = voices_df[
        (voices_df['Gender'] == gender) &
        (voices_df['Language'] == selected_language)
    ][['ShortName', 'FriendlyName']]
    voices_list = voices_filtered.apply(tuple, axis=1).tolist()
    return voices_list

# Function to perform text-to-speech


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
    selected_language = "English"
    selected_voice_name = None
    generated_file = None
    voices = get_available_voices(selected_language, selected_gender)

    if request.method == "POST":
        text = request.form.get("text")
        filename = request.form.get("filename")
        selected_gender = request.form.get("gender")
        selected_language = request.form.get("language")
        selected_voice_name = request.form.get("voice")
        rate = request.form.get("rate")
        pitch = request.form.get("pitch")

        voices = get_available_voices(selected_language, selected_gender)

        if text and filename:
            selected_voice_tuple = next(
                (v for v in voices if v[1] == selected_voice_name), None)

            if selected_voice_tuple:
                selected_voice_shortname = selected_voice_tuple[0]

                rate_str = f"{'+' if int(rate) >= 0 else ''}{int(rate)}%"
                pitch_str = f"{'+' if int(pitch) >= 0 else ''}{int(pitch)}Hz"

                clean_shortname = selected_voice_shortname.replace('-', '_')
                full_filename = f"{filename}_{clean_shortname}_rate{rate.replace('%','')}_pitch{pitch.replace('Hz','')}"

                try:
                    asyncio.run(text_to_speech(text, full_filename,
                                selected_voice_shortname, rate_str, pitch_str))
                    generated_file = f"{full_filename}.mp3"
                except Exception:
                    pass

    return render_template("index.html",
                           genders=genders,
                           languages=languages,
                           voices=voices,
                           selected_gender=selected_gender,
                           selected_language=selected_language,
                           selected_voice_name=selected_voice_name,
                           generated_file=generated_file)


@app.route("/get_voices/<gender>/<language>")
def get_voices_api(gender, language):
    voices = get_available_voices(language, gender)
    voice_names = [v[1] for v in voices]
    return jsonify(voice_names)


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(output_folder, filename, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True)

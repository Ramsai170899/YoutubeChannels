from flask import Flask, render_template, request, send_file
import edge_tts
import asyncio
import pandas as pd
import re
import nest_asyncio
import os

nest_asyncio.apply()

app = Flask(__name__)

# Function to fetch voices and filter
async def get_filtered_voices(gender):
    voices = await edge_tts.list_voices()
    df = pd.DataFrame(voices)
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'Microsoft|Online|Natural|(|)|\(\)', '', x).strip()
    )
    filtered_df = df[(df['Gender'] == gender) & (df['FriendlyName'].str.contains('English'))]
    return filtered_df[['ShortName', 'FriendlyName']].values.tolist()

@app.route('/', methods=['GET', 'POST'])
def index():
    genders = ['Female', 'Male']
    voices = []
    audio_file = None

    if request.method == 'POST':
        text = request.form['text']
        gender = request.form['gender']
        voice = request.form['voice']
        rate = request.form['rate']
        pitch = request.form['pitch']
        filename = request.form['filename']

        audio_path = f"{filename}_{voice}_{rate}_{pitch}.mp3"

        async def generate_audio():
            tts = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
            await tts.save(audio_path)

        asyncio.run(generate_audio())
        audio_file = audio_path

    elif request.method == 'GET' and 'gender' in request.args:
        gender = request.args.get('gender')
        voices = asyncio.run(get_filtered_voices(gender))

    return render_template('index.html', genders=genders, voices=voices, audio_file=audio_file)


@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)

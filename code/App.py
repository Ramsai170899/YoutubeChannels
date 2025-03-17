from flask import Flask, render_template, request, jsonify, send_file
import edge_tts
import asyncio
import pandas as pd
import re
import os

app = Flask(__name__)

async def get_filtered_voices(gender):
    voices = await edge_tts.list_voices()
    df = pd.DataFrame(voices)
    df = df[df['Gender'] == gender]
    df = df[df['FriendlyName'].str.contains('English')]
    return df[['ShortName', 'FriendlyName']].to_dict(orient='records')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_voices', methods=['POST'])
def get_voices():
    gender = request.json.get('gender')
    voices = asyncio.run(get_filtered_voices(gender))
    return jsonify(voices)

@app.route('/generate_audio', methods=['POST'])
def generate_audio():
    data = request.json
    text = re.sub(r"[*/#]", " ", data['text']).replace("—", "; ")
    voice = data['voice']
    rate = data['rate']
    pitch = data['pitch']
    filename = data['filename'] + '.mp3'
    audio_path = os.path.join('static', filename)

    async def save_audio():
        tts = edge_tts.Communicate(text=text, voice=voice, rate=rate, pitch=pitch)
        await tts.save(audio_path)

    audio_path = os.path.join('static', filename)
    asyncio.run(save_audio())
    return jsonify({'audio_file': audio_path})

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join('static', filename), as_attachment=True)

if __name__ == '__main__':
    os.makedirs('static', exist_ok=True)
    app.run(debug=True)

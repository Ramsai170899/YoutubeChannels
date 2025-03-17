@app.route('/get_voices', methods=['POST'])
def get_voices():
    gender = request.json['gender']
    voices = asyncio.run(get_voices_df(gender))
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
        tts = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
        await tts.save(audio_path)

    asyncio.run(save_audio())
    return jsonify({'audio_file': audio_path})

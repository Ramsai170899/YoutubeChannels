<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text-to-Speech App</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: #f7f9fc;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .container {
            background-color: #ffffff;
            padding: 25px;
            margin-top: 20px;
            border-radius: 10px;
            box-shadow: 0 8px 15px rgba(0, 0, 0, 0.1);
            width: 90%;
            max-width: 600px;
        }
        h2 {
            color: #4a90e2;
            text-align: center;
            margin-bottom: 20px;
        }
        label {
            font-weight: bold;
            color: #333;
        }
        textarea, select, input[type=text], button {
            width: 100%;
            padding: 10px;
            margin-bottom: 15px;
            border: 1px solid #d1d9e6;
            border-radius: 5px;
            font-size: 14px;
        }
        button {
            background-color: #4a90e2;
            color: white;
            cursor: pointer;
            border: none;
            padding: 10px;
            font-weight: bold;
        }
        button:hover {
            background-color: #357ab8;
        }
        audio {
            margin-top: 20px;
            width: 100%;
        }
</head>
<body>
    <div class="container">
        <h2>Text-to-Speech Generator</h2>
        <textarea id="text" placeholder="Enter your text here..."></textarea>

        <select id="gender" onchange="loadVoices()">
            <option value="">-- Select Gender --</option>
            <option value="Female">Female</option>
            <option value="Male">Male</option>
        </select>

        <select id="voice"></select>

        <label>Rate (%): <input type="number" id="rate" value="+0%"></label>
        <label>Pitch (Hz): <input type="number" id="pitch" value="+0Hz"></label>

        <input type="text" id="filename" placeholder="Enter filename">

        <button onclick="generateAudio()">Generate Audio</button>

        <audio id="audioPlayer" controls hidden></audio>
        <a id="downloadLink" style="display:none;">Download Audio</a>
    </div>

<script>
    async function loadVoices() {
        let gender = document.getElementById('gender').value;
        if (!gender) return;

        const response = await fetch('/get_voices', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({gender})
        });
        const voices = await response.json();

        let voiceSelect = document.getElementById('voice');
        voiceSelectClear();

        voices.forEach(([value, name]) => {
            let option = document.createElement('option');
            option.value = value;
            option.textContent = name;
            voice.appendChild(option);
        });
    }

    function voiceCleaner() {
        const voice = document.getElementById('voice');
        voice.innerHTML = '';
    }

    document.getElementById('gender').addEventListener('change', loadVoices);

    async function generateAudio() {
        const text = document.getElementById('text').value;
        const voice = document.getElementById('voice').value;
        const rate = document.getElementById('rate').value;
        const pitch = document.getElementById('pitch').value;
        const filename = document.getElementById('filename').value;

        const response = await fetch('/', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({text, voice, rate, pitch, filename})
        });

        const data = await response.json();
        let audioPlayer = new Audio(response.audio);
        audio.src = data.audio_file;
        audio.load();
    }
</script>

</body>
</html>

import streamlit as st
import edge_tts
import asyncio
import pandas as pd
import re
import os
import uuid
import shutil
import pycountry
from io import BytesIO

# Page configuration
st.set_page_config(
    page_title="Reedify",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS to match the original design
st.markdown("""
<style>
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.6));
        background-attachment: fixed;
    }
    
    /* App header and text */
    .stMarkdown h1 {
        padding-top: 1rem;
        font-size: 2.5em;
        text-align: center;
        background: linear-gradient(270deg, #f4fab6, #68d6a5, #5083c2, #b686dc, #b9cd8b);
        background-size: 400% 400%;
        background-clip: text;
        color: transparent;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: bold;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Textarea styling */
    .stTextArea textarea {
        background-color: rgba(255, 255, 255, 0.05);
        color: rgb(199, 184, 225);
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 5px;
        font-family: serif;
    }
    
    /* Input fields styling */
    .stTextInput input, .stSelectbox, .stNumberInput input {
        background-color: rgba(255, 255, 255, 0.05);
        color: rgb(199, 184, 225);
        border: 1px solid rgba(255, 255, 255, 0.4);
        border-radius: 8px;
    }
    
    /* Button styling */
    .stButton button {
        background: linear-gradient(45deg, #58cfda, #9b86df);
        color: white;
        border-radius: 8px;
        transition: 0.3s;
        border: none;
    }
    
    .stButton button:hover {
        transform: scale(1.05);
    }
    
    /* Text color for labels */
    label, .stMarkdown p {
        color: white !important;
    }
    
    /* Background image and overlay */
    .background-container {
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: -1000;
    }
    
    .background-image {
        position: absolute;
        width: 100%;
        height: 100%;
        background-image: url('https://i.pinimg.com/originals/0f/b2/88/0fb288a519fdb745d0b773d87a6aaf2e.gif');
        background-size: cover;
        background-position: center;
    }
    
    .background-overlay {
        position: absolute;
        width: 100%;
        height: 100%;
        background: linear-gradient(135deg, rgba(0, 0, 0, 0.7), rgba(0, 0, 0, 0.6));
    }
</style>

<div class="background-container">
    <div class="background-image"></div>
    <div class="background-overlay"></div>
</div>
""", unsafe_allow_html=True)

# Create directories
output_folder = "output"
temp_folder = "temp_output"
os.makedirs(output_folder, exist_ok=True)
os.makedirs(temp_folder, exist_ok=True)

# -------------------------
# TTS Helper Functions
# -------------------------


async def get_voices_data():
    voices = await edge_tts.list_voices()
    df = pd.DataFrame(voices)

    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'Microsoft|Online|Natural', '', x))
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: x.replace('(', '').replace(')', ''))
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'[-_]', ' ', x))
    df['FriendlyName'] = df['FriendlyName'].apply(
        lambda x: re.sub(r'\s+', ' ', x).strip())

    def get_language_name(locale):
        language_code = locale.split('-')[0]
        try:
            language = pycountry.languages.get(alpha_2=language_code)
            return language.name if language else 'Unknown'
        except AttributeError:
            return 'Unknown'

    df['Language'] = df['Locale'].apply(get_language_name)
    return df


@st.cache_data
def get_voices_df():
    """
    A cached wrapper for the async function that gets voices data.
    This function runs the async function and returns the result.
    """
    return asyncio.run(get_voices_data())


def get_available_voices(selected_language, gender):
    voices_filtered = voices_df[
        (voices_df['Gender'] == gender) &
        (voices_df['Language'] == selected_language)
    ][['ShortName', 'FriendlyName']]
    voices_list = voices_filtered.apply(tuple, axis=1).tolist()
    return voices_list


async def text_to_speech(text, voice="en-US-GuyNeural", rate="+0%", pitch="+0Hz"):
    text = re.sub(r"[*/#₹-]", " ", text).replace("—", ". ")
    temp_filename = f"{uuid.uuid4().hex}.mp3"
    temp_path = os.path.join(temp_folder, temp_filename)

    tts = edge_tts.Communicate(text, voice=voice, rate=rate, pitch=pitch)
    await tts.save(temp_path)

    # Read the file and return as bytes
    with open(temp_path, "rb") as f:
        audio_bytes = f.read()

    # Clean up temp file
    os.remove(temp_path)

    return audio_bytes

# Initialize voices dataframe
if 'voices_df' not in st.session_state:
    st.session_state.voices_df = get_voices_df()
voices_df = st.session_state.voices_df
languages = sorted(voices_df['Language'].unique().tolist())

# -------------------------
# Streamlit App Interface
# -------------------------

# App title
st.markdown("<h1>Reedify</h1>", unsafe_allow_html=True)

# Create two columns: left for text input, right for controls
col1, col2 = st.columns([3, 1])

with col1:
    # Text input area
    text_input = st.text_area(
        "", placeholder="Paste or type your script...", height=400)

with col2:
    # Controls
    filename_input = st.text_input("Filename:", placeholder="Output filename")

    selected_language = st.selectbox("Language:", languages, index=languages.index(
        "English") if "English" in languages else 0)

    genders = ["Male", "Female"]
    selected_gender = st.selectbox("Gender:", genders)

    # Get available voices based on language and gender
    voices = get_available_voices(selected_language, selected_gender)
    voice_names = [v[1] for v in voices]

    # Check if voice_names has entries before creating selectbox
    if voice_names:
        selected_voice_name = st.selectbox("Voice:", voice_names)
        # Find the corresponding voice tuple
        selected_voice_tuple = next(
            (v for v in voices if v[1] == selected_voice_name), None)
        selected_voice = selected_voice_tuple[0] if selected_voice_tuple else None
    else:
        st.warning(
            f"No voices available for {selected_gender} gender in {selected_language}. Please try another combination.")
        selected_voice = None

    # Rate and pitch controls
    rate_value = st.number_input(
        "Rate:", min_value=-100, max_value=100, value=10)
    pitch_value = st.number_input(
        "Pitch:", min_value=-100, max_value=100, value=-10)

    # Preview button
    preview_button = st.button("🗘 Preview", use_container_width=True)

# Audio output area (centered)
audio_container = st.container()

# Processing logic
if preview_button and text_input and filename_input and selected_voice:
    with st.spinner("Generating audio preview..."):
        rate_str = f"{'+' if int(rate_value) >= 0 else ''}{int(rate_value)}%"
        pitch_str = f"{'+' if int(pitch_value) >= 0 else ''}{int(pitch_value)}Hz"

        # Generate audio
        audio_bytes = asyncio.run(text_to_speech(
            text_input, selected_voice, rate_str, pitch_str))

        # Store the generated audio in session state for later use
        st.session_state.audio_bytes = audio_bytes
        st.session_state.filename = filename_input
        st.session_state.voice_name = selected_voice.replace('-', '_')

        # Display audio player
        with audio_container:
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                st.audio(audio_bytes, format="audio/mp3")

                # Save button
                if st.button("Save & Download", use_container_width=True):
                    final_filename = f"{st.session_state.filename}-{st.session_state.voice_name}.mp3"

                    # Prepare download button
                    st.download_button(
                        label="Download Audio",
                        data=st.session_state.audio_bytes,
                        file_name=final_filename,
                        mime="audio/mp3",
                        use_container_width=True
                    )

# Add quick info on how to use
with st.expander("About Reedify"):
    st.markdown("""
    **Reedify** is a text-to-speech converter that uses the Edge TTS engine.
    
    **How to use:**
    1. Enter your text in the left panel
    2. Enter a filename for your output file
    3. Select language, gender, voice, rate, and pitch
    4. Click the preview button to hear the audio
    5. Download the audio file when you're happy with it
    
    _Built with Streamlit and Edge TTS_
    """)

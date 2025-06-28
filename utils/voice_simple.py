"""
Simple Voice Interface using OpenAI TTS API
Provides text-to-speech for water quality responses
"""

import os
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI
import streamlit as st
import base64
from io import BytesIO

load_dotenv()

class SimpleVoiceAssistant:
    """Simple voice assistant using OpenAI TTS"""
    
    def __init__(self):
        try:
            self.client = OpenAI()
            self.enabled = True
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            self.client = None
            self.enabled = False
    
    def text_to_speech(self, text: str, voice: str = "alloy") -> Optional[bytes]:
        """Convert text to speech using OpenAI TTS"""
        if not self.enabled:
            return None
        
        try:
            # Generate speech
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            
            # Get audio bytes
            audio_bytes = BytesIO()
            for chunk in response.iter_bytes():
                audio_bytes.write(chunk)
            
            return audio_bytes.getvalue()
            
        except Exception as e:
            st.error(f"Error generating speech: {e}")
            return None
    
    def create_audio_player(self, audio_bytes: bytes) -> str:
        """Create HTML audio player for the audio bytes"""
        # Encode audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode()
        
        # Create audio HTML
        audio_html = f"""
        <audio controls autoplay>
            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
            Your browser does not support the audio element.
        </audio>
        """
        
        return audio_html


def create_simple_voice_interface(db, ai):
    """Create simple voice interface for Streamlit"""
    
    # Initialize voice assistant
    if 'simple_voice' not in st.session_state:
        st.session_state.simple_voice = SimpleVoiceAssistant()
        st.session_state.voice_history = []
    
    voice = st.session_state.simple_voice
    
    if not voice.enabled:
        st.warning("Voice features require OpenAI API key")
        return
    
    # Voice settings
    col1, col2 = st.columns([3, 1])
    
    with col2:
        voice_type = st.selectbox(
            "Voice:",
            ["alloy", "echo", "fable", "onyx", "nova", "shimmer"],
            help="Select the voice type for responses"
        )
    
    with col1:
        # Question input
        question = st.text_input(
            "Ask about water quality (responses will be spoken):",
            placeholder="e.g., Is the water in Atlanta safe to drink?",
            key="voice_question"
        )
    
    if st.button("🎤 Ask & Listen", type="primary", use_container_width=True):
        if question:
            with st.spinner("Getting answer..."):
                # Get AI response
                response = ai.chat_query(question)
                
                # Generate speech
                with st.spinner("Generating speech..."):
                    audio_bytes = voice.text_to_speech(response, voice=voice_type)
                
                if audio_bytes:
                    # Display response text
                    st.markdown("### Answer:")
                    st.write(response)
                    
                    # Display audio player
                    st.markdown("### 🔊 Listen to Response:")
                    audio_html = voice.create_audio_player(audio_bytes)
                    st.markdown(audio_html, unsafe_allow_html=True)
                    
                    # Save to history
                    st.session_state.voice_history.append({
                        'question': question,
                        'response': response,
                        'voice': voice_type
                    })
    
    # Quick questions
    st.markdown("### 💡 Quick Questions")
    
    quick_questions = [
        "What are the most common water violations in Georgia?",
        "Is it safe to drink tap water with lead violations?",
        "How often should water be tested?",
        "What does a boil water advisory mean?"
    ]
    
    cols = st.columns(2)
    for i, q in enumerate(quick_questions):
        with cols[i % 2]:
            if st.button(q, key=f"quick_{i}"):
                st.session_state.voice_question = q
                st.rerun()
    
    # Voice history
    if st.session_state.voice_history:
        st.markdown("### 📜 Voice History")
        for i, item in enumerate(reversed(st.session_state.voice_history[-5:])):
            with st.expander(f"Q: {item['question'][:50]}..."):
                st.write(f"**Question:** {item['question']}")
                st.write(f"**Response:** {item['response']}")
                st.write(f"**Voice:** {item['voice']}")
                
                # Regenerate audio button
                if st.button(f"🔄 Replay", key=f"replay_{i}"):
                    audio_bytes = voice.text_to_speech(item['response'], voice=item['voice'])
                    if audio_bytes:
                        audio_html = voice.create_audio_player(audio_bytes)
                        st.markdown(audio_html, unsafe_allow_html=True)
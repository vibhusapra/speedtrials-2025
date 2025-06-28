"""
Streamlit Component for Realtime Voice Interface
Bridges the frontend JavaScript with the backend WebSocket
"""

import streamlit as st
import streamlit.components.v1 as components
import json
import base64
from typing import Dict, Any, Optional
import threading
import time
from .realtime_voice import RealtimeVoiceAssistant

class VoiceComponent:
    """Streamlit component for voice interaction"""
    
    def __init__(self):
        if 'voice_assistant' not in st.session_state:
            st.session_state.voice_assistant = RealtimeVoiceAssistant()
            st.session_state.voice_connected = False
            st.session_state.voice_transcript = []
            st.session_state.audio_buffer = []
        
        self.assistant = st.session_state.voice_assistant
        
    def render(self):
        """Render the voice interface component"""
        
        # Load JavaScript
        import os
        js_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'voice_interface.js')
        with open(js_path, 'r') as f:
            js_code = f.read()
        
        # HTML template with embedded JavaScript
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{
                    font-family: sans-serif;
                    padding: 20px;
                    background: #f0f2f6;
                    margin: 0;
                }}
                .voice-container {{
                    max-width: 600px;
                    margin: 0 auto;
                }}
                .controls {{
                    display: flex;
                    gap: 10px;
                    margin-bottom: 20px;
                }}
                button {{
                    padding: 10px 20px;
                    border: none;
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 16px;
                    transition: all 0.3s;
                }}
                .btn-primary {{
                    background: #ff6b6b;
                    color: white;
                }}
                .btn-primary:hover {{
                    background: #ff5252;
                }}
                .btn-secondary {{
                    background: #4CAF50;
                    color: white;
                }}
                .btn-secondary:hover {{
                    background: #45a049;
                }}
                button:disabled {{
                    opacity: 0.5;
                    cursor: not-allowed;
                }}
                .status {{
                    padding: 10px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    text-align: center;
                }}
                .status.recording {{
                    background: #ffebee;
                    color: #c62828;
                    animation: pulse 1.5s infinite;
                }}
                .status.ready {{
                    background: #e8f5e9;
                    color: #2e7d32;
                }}
                .status.processing {{
                    background: #fff3e0;
                    color: #e65100;
                }}
                @keyframes pulse {{
                    0% {{ opacity: 1; }}
                    50% {{ opacity: 0.7; }}
                    100% {{ opacity: 1; }}
                }}
                .audio-visualizer {{
                    height: 60px;
                    background: #333;
                    border-radius: 5px;
                    margin: 20px 0;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 3px;
                    padding: 0 20px;
                }}
                .audio-bar {{
                    width: 4px;
                    height: 20px;
                    background: #4CAF50;
                    border-radius: 2px;
                    transition: height 0.1s;
                }}
                .instructions {{
                    background: #e3f2fd;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="voice-container">
                <div class="status ready" id="status">
                    🎤 Ready to listen
                </div>
                
                <div class="instructions">
                    <strong>How to use:</strong><br>
                    1. Click "Start Listening" and allow microphone access<br>
                    2. Speak your question about water quality<br>
                    3. The AI will respond with voice<br>
                    4. Click "Stop Listening" when done
                </div>
                
                <div class="controls">
                    <button id="initBtn" class="btn-secondary" onclick="initializeVoice()">
                        🔌 Initialize
                    </button>
                    <button id="startBtn" class="btn-primary" onclick="toggleRecording()" disabled>
                        🎤 Start Listening
                    </button>
                </div>
                
                <div class="audio-visualizer" id="visualizer">
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                    <div class="audio-bar"></div>
                </div>
            </div>
            
            <script>
                {js_code}
                
                let isRecording = false;
                let isInitialized = false;
                
                function updateStatus(message, className) {{
                    const status = document.getElementById('status');
                    status.textContent = message;
                    status.className = 'status ' + className;
                }}
                
                async function initializeVoice() {{
                    const initBtn = document.getElementById('initBtn');
                    initBtn.disabled = true;
                    initBtn.textContent = '⏳ Initializing...';
                    
                    updateStatus('Initializing microphone...', 'processing');
                    
                    // Initialize voice interface
                    const success = await initVoice();
                    
                    if (success) {{
                        isInitialized = true;
                        updateStatus('✅ Microphone ready', 'ready');
                        document.getElementById('startBtn').disabled = false;
                        initBtn.textContent = '✅ Initialized';
                    }} else {{
                        updateStatus('❌ Microphone access denied', 'error');
                        initBtn.disabled = false;
                        initBtn.textContent = '🔌 Retry Initialize';
                    }}
                }}
                
                function toggleRecording() {{
                    const btn = document.getElementById('startBtn');
                    
                    if (!isRecording) {{
                        startRecording();
                        isRecording = true;
                        btn.textContent = '⏹️ Stop Listening';
                        btn.style.background = '#f44336';
                        updateStatus('🔴 Listening... Speak now!', 'recording');
                        animateVisualizer(true);
                    }} else {{
                        stopRecording();
                        isRecording = false;
                        btn.textContent = '🎤 Start Listening';
                        btn.style.background = '#ff6b6b';
                        updateStatus('✅ Ready to listen', 'ready');
                        animateVisualizer(false);
                    }}
                }}
                
                function animateVisualizer(active) {{
                    const bars = document.querySelectorAll('.audio-bar');
                    
                    if (active) {{
                        // Animate bars
                        setInterval(() => {{
                            bars.forEach(bar => {{
                                const height = Math.random() * 40 + 10;
                                bar.style.height = height + 'px';
                            }});
                        }}, 100);
                    }} else {{
                        // Reset bars
                        bars.forEach(bar => {{
                            bar.style.height = '20px';
                        }});
                    }}
                }}
                
                // Listen for Enter key
                document.addEventListener('keydown', (e) => {{
                    if (e.key === 'Enter' && isInitialized && !isRecording) {{
                        toggleRecording();
                    }}
                }});
            </script>
        </body>
        </html>
        """
        
        # Render component
        component_value = components.html(
            html_template,
            height=400,
            scrolling=False
        )
        
        return component_value
    
    def connect_websocket(self):
        """Connect to OpenAI Realtime API"""
        
        def on_audio_response(audio_bytes):
            """Handle audio response from API"""
            # Convert to base64 for frontend
            audio_base64 = base64.b64encode(audio_bytes).decode()
            st.session_state.audio_buffer.append(audio_base64)
        
        def on_transcript(role, content):
            """Handle transcript updates"""
            if role == 'assistant':
                st.session_state.voice_transcript.append({
                    'role': 'assistant',
                    'content': content,
                    'timestamp': time.time()
                })
            elif role == 'assistant_partial':
                # Update partial transcript
                if st.session_state.voice_transcript and st.session_state.voice_transcript[-1]['role'] == 'assistant_partial':
                    st.session_state.voice_transcript[-1]['content'] += content
                else:
                    st.session_state.voice_transcript.append({
                        'role': 'assistant_partial',
                        'content': content,
                        'timestamp': time.time()
                    })
        
        def on_error(error):
            """Handle errors"""
            st.error(f"Voice Error: {error}")
        
        # Connect with callbacks
        connected = self.assistant.connect(
            on_response=on_audio_response,
            on_transcript=on_transcript,
            on_error=on_error
        )
        
        st.session_state.voice_connected = connected
        return connected
    
    def process_audio_stream(self, audio_base64: str):
        """Process incoming audio from frontend"""
        if st.session_state.voice_connected:
            # Decode base64 to bytes
            audio_bytes = base64.b64decode(audio_base64)
            
            # Send to API
            self.assistant.send_audio(audio_bytes)
    
    def update_context(self, context: Dict[str, Any]):
        """Update voice assistant context"""
        if st.session_state.voice_connected:
            self.assistant.update_context(context)


def create_realtime_voice_interface(db, ai):
    """Create the main voice interface for Streamlit"""
    
    st.markdown("### 🎙️ Real-time Voice Conversation")
    
    # Initialize component
    voice_component = VoiceComponent()
    
    # Connection controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔌 Connect to Voice API", disabled=st.session_state.get('voice_connected', False)):
            with st.spinner("Connecting to OpenAI Realtime API..."):
                if voice_component.connect_websocket():
                    st.success("Connected! You can now start talking.")
                else:
                    st.error("Failed to connect. Please check your API key.")
    
    with col2:
        if st.button("🔄 Disconnect", disabled=not st.session_state.get('voice_connected', False)):
            voice_component.assistant.disconnect()
            st.session_state.voice_connected = False
            st.info("Disconnected from voice API")
    
    with col3:
        # Context selector
        if st.session_state.get('voice_connected', False):
            if st.checkbox("Add city context"):
                city = st.text_input("City name:", placeholder="e.g., Atlanta")
                if city:
                    # Get city data
                    city_data = db.query_df("""
                        SELECT 
                            COUNT(DISTINCT p.PWSID) as systems,
                            SUM(p.POPULATION_SERVED_COUNT) as population,
                            COUNT(DISTINCT v.VIOLATION_ID) as violations
                        FROM pub_water_systems p
                        LEFT JOIN violations_enforcement v ON p.PWSID = v.PWSID
                        WHERE UPPER(p.CITY_NAME) LIKE ?
                    """, (f"%{city.upper()}%",))
                    
                    if not city_data.empty:
                        context = {
                            'city_name': city,
                            'water_system': {
                                'name': f"{city} Water Systems",
                                'population': int(city_data.iloc[0]['population'] or 0),
                                'violations': int(city_data.iloc[0]['violations'] or 0),
                                'systems': int(city_data.iloc[0]['systems'] or 0)
                            }
                        }
                        voice_component.update_context(context)
                        st.success(f"Added context for {city}")
    
    # Render voice interface
    if st.session_state.get('voice_connected', False):
        voice_component.render()
        
        # Display transcript
        st.markdown("### 📝 Conversation Transcript")
        
        transcript_container = st.container()
        with transcript_container:
            for entry in st.session_state.get('voice_transcript', []):
                if entry['role'] == 'user':
                    st.markdown(f"**🗣️ You:** {entry['content']}")
                elif entry['role'] in ['assistant', 'assistant_partial']:
                    st.markdown(f"**🤖 Assistant:** {entry['content']}")
                
        # Audio playback handler
        if st.session_state.get('audio_buffer'):
            # Play the audio through frontend
            for audio_base64 in st.session_state.audio_buffer:
                st.markdown(f"""
                <script>
                    playAudio('{audio_base64}');
                </script>
                """, unsafe_allow_html=True)
            
            # Clear buffer
            st.session_state.audio_buffer = []
    
    else:
        st.info("👆 Click 'Connect to Voice API' to start voice conversation")
        
        # Show example questions
        st.markdown("### 💭 Example Voice Questions")
        
        examples = [
            "What's the water quality like in Atlanta?",
            "Are there any lead violations in my area?",
            "How do I know if my water is safe to drink?",
            "What should I do if there's a boil water advisory?",
            "Can you explain what a Stage 2 DBP violation means?"
        ]
        
        for example in examples:
            st.markdown(f"• {example}")
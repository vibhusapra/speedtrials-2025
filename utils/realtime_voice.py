"""
OpenAI Realtime Voice API Implementation
Provides speech-to-speech interaction for water quality queries
"""

import os
import json
import base64
import time
import websocket
import threading
from typing import Optional, Callable, Dict, Any
from queue import Queue
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

class RealtimeVoiceAssistant:
    """Handle real-time voice interactions using OpenAI Realtime API"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.ws = None
        self.is_connected = False
        self.audio_queue = Queue()
        self.response_callback = None
        self.transcript_callback = None
        self.error_callback = None
        self.context = {}
        
        # WebSocket URL with model
        self.url = "wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-12-17"
        
    def connect(self, on_response: Callable = None, on_transcript: Callable = None, on_error: Callable = None):
        """Connect to OpenAI Realtime API"""
        self.response_callback = on_response
        self.transcript_callback = on_transcript
        self.error_callback = on_error
        
        headers = [
            f"Authorization: Bearer {self.api_key}",
            "OpenAI-Beta: realtime=v1"
        ]
        
        self.ws = websocket.WebSocketApp(
            self.url,
            header=headers,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        # Run WebSocket in separate thread
        ws_thread = threading.Thread(target=self.ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection
        for _ in range(50):  # 5 second timeout
            if self.is_connected:
                return True
            time.sleep(0.1)
        
        return False
    
    def on_open(self, ws):
        """Handle WebSocket connection open"""
        print("Connected to OpenAI Realtime API")
        self.is_connected = True
        
        # Configure session for water quality assistant
        session_config = {
            "type": "session.update",
            "session": {
                "modalities": ["text", "audio"],
                "instructions": """You are a helpful water quality assistant for Georgia residents. 
                You help people understand their drinking water quality, violations, and safety concerns.
                Keep responses concise and clear. Focus on the most important information.
                If the user mentions a specific city or water system, use that context in your response.
                Always provide practical advice when discussing water quality issues.""",
                "voice": "alloy",
                "input_audio_format": "pcm16",
                "output_audio_format": "pcm16",
                "input_audio_transcription": {
                    "model": "whisper-1"
                },
                "turn_detection": {
                    "type": "server_vad",
                    "threshold": 0.5,
                    "prefix_padding_ms": 300,
                    "silence_duration_ms": 200
                },
                "temperature": 0.8,
                "max_response_output_tokens": 4096
            }
        }
        
        self.send_message(session_config)
        
        # Send initial context if available
        if self.context:
            self.update_context(self.context)
    
    def on_message(self, ws, message):
        """Handle incoming WebSocket messages"""
        try:
            data = json.loads(message)
            event_type = data.get('type', '')
            
            if event_type == 'session.created':
                print("Session created successfully")
                
            elif event_type == 'conversation.item.created':
                # Handle conversation updates
                item = data.get('item', {})
                if item.get('role') == 'assistant' and self.transcript_callback:
                    self.transcript_callback('assistant', item.get('content', []))
                    
            elif event_type == 'response.audio.delta':
                # Handle audio chunks
                audio_base64 = data.get('delta', '')
                if audio_base64 and self.response_callback:
                    audio_bytes = base64.b64decode(audio_base64)
                    self.response_callback(audio_bytes)
                    
            elif event_type == 'response.audio_transcript.delta':
                # Handle transcript updates
                transcript = data.get('delta', '')
                if transcript and self.transcript_callback:
                    self.transcript_callback('assistant_partial', transcript)
                    
            elif event_type == 'input_audio_buffer.speech_started':
                print("User started speaking")
                
            elif event_type == 'input_audio_buffer.speech_stopped':
                print("User stopped speaking")
                
            elif event_type == 'response.done':
                # Response completed
                if self.transcript_callback:
                    self.transcript_callback('complete', '')
                    
            elif event_type == 'error':
                error_msg = data.get('error', {}).get('message', 'Unknown error')
                print(f"API Error: {error_msg}")
                if self.error_callback:
                    self.error_callback(error_msg)
                    
        except Exception as e:
            print(f"Error processing message: {e}")
            if self.error_callback:
                self.error_callback(str(e))
    
    def on_error(self, ws, error):
        """Handle WebSocket errors"""
        print(f"WebSocket error: {error}")
        self.is_connected = False
        if self.error_callback:
            self.error_callback(str(error))
    
    def on_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close"""
        print("WebSocket connection closed")
        self.is_connected = False
    
    def send_message(self, message: dict):
        """Send message to the API"""
        if self.ws and self.is_connected:
            self.ws.send(json.dumps(message))
    
    def send_audio(self, audio_bytes: bytes):
        """Send audio data to the API"""
        if not self.is_connected:
            return
        
        # Convert audio to base64
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        # Send audio buffer
        message = {
            "type": "input_audio_buffer.append",
            "audio": audio_base64
        }
        
        self.send_message(message)
    
    def commit_audio(self):
        """Commit the audio buffer for processing"""
        if self.is_connected:
            self.send_message({"type": "input_audio_buffer.commit"})
    
    def clear_audio(self):
        """Clear the audio buffer"""
        if self.is_connected:
            self.send_message({"type": "input_audio_buffer.clear"})
    
    def send_text(self, text: str):
        """Send text message"""
        if not self.is_connected:
            return
        
        # Create conversation item
        message = {
            "type": "conversation.item.create",
            "item": {
                "type": "message",
                "role": "user",
                "content": [{
                    "type": "input_text",
                    "text": text
                }]
            }
        }
        
        self.send_message(message)
        
        # Trigger response
        self.send_message({"type": "response.create"})
    
    def update_context(self, context: Dict[str, Any]):
        """Update conversation context"""
        self.context = context
        
        if self.is_connected and context:
            # Build context message
            context_text = "Current context:\n"
            
            if 'city_name' in context:
                context_text += f"- User is asking about {context['city_name']}\n"
            
            if 'water_system' in context:
                system = context['water_system']
                context_text += f"- Water System: {system.get('name', 'Unknown')}\n"
                context_text += f"- Population Served: {system.get('population', 'Unknown')}\n"
                context_text += f"- Active Violations: {system.get('violations', 'Unknown')}\n"
            
            # Send context as system message
            message = {
                "type": "conversation.item.create",
                "item": {
                    "type": "message",
                    "role": "system",
                    "content": [{
                        "type": "text",
                        "text": context_text
                    }]
                }
            }
            
            self.send_message(message)
    
    def interrupt(self):
        """Interrupt the current response"""
        if self.is_connected:
            self.send_message({"type": "response.cancel"})
    
    def disconnect(self):
        """Disconnect from the API"""
        if self.ws:
            self.ws.close()
        self.is_connected = False
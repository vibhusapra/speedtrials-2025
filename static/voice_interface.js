/**
 * Voice Interface for OpenAI Realtime API
 * Handles audio capture, streaming, and playback
 */

class VoiceInterface {
    constructor() {
        this.mediaRecorder = null;
        this.audioContext = null;
        this.isRecording = false;
        this.audioQueue = [];
        this.audioWorkletNode = null;
        this.stream = null;
        
        // Audio settings for OpenAI Realtime API
        this.sampleRate = 24000;
        this.channels = 1;
        
        // Callbacks
        this.onAudioData = null;
        this.onError = null;
        this.onStatusChange = null;
    }
    
    async initialize() {
        try {
            // Request microphone permission
            this.stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    channelCount: this.channels,
                    sampleRate: this.sampleRate,
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                } 
            });
            
            // Create audio context
            this.audioContext = new AudioContext({ sampleRate: this.sampleRate });
            
            // Set up audio processing
            await this.setupAudioProcessing();
            
            return true;
        } catch (error) {
            console.error('Failed to initialize audio:', error);
            if (this.onError) {
                this.onError(`Microphone access denied: ${error.message}`);
            }
            return false;
        }
    }
    
    async setupAudioProcessing() {
        const source = this.audioContext.createMediaStreamSource(this.stream);
        
        // Create script processor for audio capture (using deprecated API for simplicity)
        // In production, use AudioWorklet
        const bufferSize = 4096;
        const scriptProcessor = this.audioContext.createScriptProcessor(bufferSize, 1, 1);
        
        scriptProcessor.onaudioprocess = (event) => {
            if (!this.isRecording) return;
            
            const inputData = event.inputBuffer.getChannelData(0);
            
            // Convert Float32Array to PCM16
            const pcm16 = this.float32ToPCM16(inputData);
            
            // Send audio data
            if (this.onAudioData) {
                this.onAudioData(pcm16);
            }
        };
        
        // Connect audio nodes
        source.connect(scriptProcessor);
        scriptProcessor.connect(this.audioContext.destination);
    }
    
    float32ToPCM16(float32Array) {
        const pcm16 = new Int16Array(float32Array.length);
        for (let i = 0; i < float32Array.length; i++) {
            // Convert float32 (-1 to 1) to int16 (-32768 to 32767)
            const s = Math.max(-1, Math.min(1, float32Array[i]));
            pcm16[i] = s < 0 ? s * 32768 : s * 32767;
        }
        return pcm16.buffer;
    }
    
    pcm16ToFloat32(arrayBuffer) {
        const pcm16 = new Int16Array(arrayBuffer);
        const float32 = new Float32Array(pcm16.length);
        
        for (let i = 0; i < pcm16.length; i++) {
            float32[i] = pcm16[i] / (pcm16[i] < 0 ? 32768 : 32767);
        }
        
        return float32;
    }
    
    startRecording() {
        if (!this.audioContext) {
            if (this.onError) {
                this.onError('Audio not initialized. Please allow microphone access.');
            }
            return false;
        }
        
        this.isRecording = true;
        if (this.onStatusChange) {
            this.onStatusChange('recording');
        }
        
        // Resume audio context if suspended
        if (this.audioContext.state === 'suspended') {
            this.audioContext.resume();
        }
        
        return true;
    }
    
    stopRecording() {
        this.isRecording = false;
        if (this.onStatusChange) {
            this.onStatusChange('stopped');
        }
    }
    
    async playAudio(audioData) {
        if (!this.audioContext) return;
        
        try {
            // Convert PCM16 to Float32
            const float32Data = this.pcm16ToFloat32(audioData);
            
            // Create audio buffer
            const audioBuffer = this.audioContext.createBuffer(
                1, // mono
                float32Data.length,
                this.sampleRate
            );
            
            // Copy data to buffer
            audioBuffer.getChannelData(0).set(float32Data);
            
            // Create and play source
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start();
            
        } catch (error) {
            console.error('Error playing audio:', error);
        }
    }
    
    cleanup() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        if (this.audioContext) {
            this.audioContext.close();
        }
        this.mediaRecorder = null;
        this.audioContext = null;
        this.isRecording = false;
    }
}

// Streamlit component communication
function sendMessageToStreamlit(type, data) {
    if (window.parent && window.parent.postMessage) {
        window.parent.postMessage({
            type: type,
            data: data
        }, '*');
    }
}

// Global voice interface instance
let voiceInterface = null;

// Initialize voice interface
async function initVoice() {
    voiceInterface = new VoiceInterface();
    
    voiceInterface.onAudioData = (audioData) => {
        // Send audio data to Streamlit
        sendMessageToStreamlit('audio_data', {
            audio: arrayBufferToBase64(audioData)
        });
    };
    
    voiceInterface.onError = (error) => {
        sendMessageToStreamlit('error', { message: error });
    };
    
    voiceInterface.onStatusChange = (status) => {
        sendMessageToStreamlit('status', { status: status });
    };
    
    const initialized = await voiceInterface.initialize();
    sendMessageToStreamlit('initialized', { success: initialized });
    
    return initialized;
}

// Start recording
function startRecording() {
    if (voiceInterface) {
        const started = voiceInterface.startRecording();
        sendMessageToStreamlit('recording_started', { success: started });
    }
}

// Stop recording
function stopRecording() {
    if (voiceInterface) {
        voiceInterface.stopRecording();
        sendMessageToStreamlit('recording_stopped', {});
    }
}

// Play audio from Streamlit
function playAudio(base64Audio) {
    if (voiceInterface) {
        const audioData = base64ToArrayBuffer(base64Audio);
        voiceInterface.playAudio(audioData);
    }
}

// Utility functions
function arrayBufferToBase64(buffer) {
    const bytes = new Uint8Array(buffer);
    let binary = '';
    for (let i = 0; i < bytes.byteLength; i++) {
        binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
}

function base64ToArrayBuffer(base64) {
    const binaryString = atob(base64);
    const len = binaryString.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = binaryString.charCodeAt(i);
    }
    return bytes.buffer;
}

// Listen for messages from Streamlit
window.addEventListener('message', (event) => {
    const message = event.data;
    
    switch (message.type) {
        case 'init':
            initVoice();
            break;
        case 'start_recording':
            startRecording();
            break;
        case 'stop_recording':
            stopRecording();
            break;
        case 'play_audio':
            playAudio(message.audio);
            break;
        case 'cleanup':
            if (voiceInterface) {
                voiceInterface.cleanup();
            }
            break;
    }
});
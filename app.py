#!/usr/bin/env python
"""
Voice Changer API.
Record your voice in the browser, apply effects, download the result.
"""

from flask import Flask, request, send_file, render_template_string
import subprocess
import tempfile
import os
import base64

app = Flask(__name__)

EFFECTS = {
    "echo": ["-af", "aecho=0.8:0.9:100|200:0.5|0.3"],
    "robot":["-af", "afftfilt=real='hypot(re,im)*sin(0)':imag='hypot(re,im)*cos(0)':win_size=512:overlap=0.75,volume=3.5"],
    # # TODO: Add whisper effect for student exercise
    # "reverse": ["-af", "areverse"],
}

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Voice Changer</title>
    <style>
        * { font-family: system-ui, sans-serif; }
        body { 
            max-width: 600px; 
            margin: 50px auto; 
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .card {
            background: white;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { 
            margin: 0 0 10px 0;
            font-size: 28px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 25px;
        }
        .form-group {
            margin-bottom: 20px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        select {
            width: 100%;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            background: white;
        }
        button {
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            margin-bottom: 10px;
        }
        .record-btn {
            background: #e74c3c;
            color: white;
        }
        .record-btn.recording {
            background: #333;
            animation: pulse 1s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.6; }
        }
        .transform-btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .transform-btn:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        button:hover:not(:disabled) {
            opacity: 0.9;
        }
        .audio-preview {
            width: 100%;
            margin: 10px 0;
        }
        .status {
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            display: none;
        }
        .status.show {
            display: block;
        }
        .status.recording {
            background: #fdeaea;
            color: #e74c3c;
        }
        .status.processing {
            background: #eaf0fd;
            color: #667eea;
        }
        .status.ready {
            background: #eafde7;
            color: #27ae60;
        }
        .effects-preview {
            margin-top: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 14px;
        }
        .effects-preview code {
            color: #667eea;
        }
        .result-section {
            margin-top: 20px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            display: none;
        }
        .result-section.show {
            display: block;
        }
        .comparison {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .comparison-item {
            background: #1a1a2e;
            border-radius: 8px;
            padding: 15px;
        }
        .comparison-item h3 {
            margin: 0 0 10px 0;
            font-size: 14px;
            color: #fff;
        }
        .comparison-canvas {
            width: 100%;
            height: 80px;
            display: block;
            border-radius: 4px;
        }
        .comparison-item audio {
            width: 100%;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>🎤 Voice Changer</h1>
        <p class="subtitle">Record your voice, apply effects, have fun!</p>
        
        <div class="status" id="status"></div>
        
        <div class="form-group">
            <label>1. Record your voice</label>
            <button type="button" class="record-btn" id="recordBtn">
                🎙️ Click to Start Recording
            </button>
        </div>
        
        <div class="form-group">
            <label>2. Select effect</label>
            <select id="effect">
                <option value="robot">Robot</option>
                <option value="echo">Echo</option>
            </select>
        </div>
        
        <button type="button" class="transform-btn" id="transformBtn" disabled>
            Transform!
        </button>
        
        <div class="result-section" id="resultSection">
            <label>3. Compare results</label>
            <div class="comparison">
                <div class="comparison-item">
                    <h3>Original</h3>
                    <canvas id="compareOriginal" class="comparison-canvas" width="400" height="160"></canvas>
                    <audio id="preview" controls></audio>
                </div>
                <div class="comparison-item">
                    <h3>Transformed</h3>
                    <canvas id="compareResult" class="comparison-canvas" width="400" height="160"></canvas>
                    <audio id="result" controls></audio>
                </div>
            </div>
        </div>
        
    </div>

    <script>
        let mediaRecorder;
        let audioChunks = [];
        let audioBlob = null;
        let isRecording = false;
        let originalAudioBuffer = null;
        
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        const recordBtn = document.getElementById('recordBtn');
        const transformBtn = document.getElementById('transformBtn');
        const preview = document.getElementById('preview');
        const result = document.getElementById('result');
        const resultSection = document.getElementById('resultSection');
        const status = document.getElementById('status');
        const effectSelect = document.getElementById('effect');
        
        function showStatus(message, type) {
            status.textContent = message;
            status.className = 'status show ' + type;
        }
        
        function hideStatus() {
            status.className = 'status';
        }
        
        // Draw waveform on canvas
        function drawWaveform(canvas, audioBuffer, color) {
            const ctx = canvas.getContext('2d');
            const width = canvas.width;
            const height = canvas.height;
            
            ctx.fillStyle = '#1a1a2e';
            ctx.fillRect(0, 0, width, height);
            
            const data = audioBuffer.getChannelData(0);
            const step = Math.ceil(data.length / width);
            const amp = height / 2;
            
            ctx.fillStyle = color;
            
            for (let i = 0; i < width; i++) {
                let min = 1.0;
                let max = -1.0;
                
                for (let j = 0; j < step; j++) {
                    const index = (i * step) + j;
                    if (index < data.length) {
                        const datum = data[index];
                        if (datum < min) min = datum;
                        if (datum > max) max = datum;
                    }
                }
                
                const barHeight = Math.max(1, (max - min) * amp);
                const y = (1 - max) * amp;
                
                ctx.fillRect(i, y, 1, barHeight);
            }
            
            ctx.strokeStyle = 'rgba(255,255,255,0.2)';
            ctx.beginPath();
            ctx.moveTo(0, amp);
            ctx.lineTo(width, amp);
            ctx.stroke();
        }
        
        // Decode audio blob to AudioBuffer
        async function decodeAudio(blob) {
            const arrayBuffer = await blob.arrayBuffer();
            return await audioContext.decodeAudioData(arrayBuffer);
        }
        
        // Initialize microphone
        async function initMicrophone() {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                mediaRecorder = new MediaRecorder(stream);
                
                mediaRecorder.ondataavailable = (e) => {
                    audioChunks.push(e.data);
                };
                
                mediaRecorder.onstop = async () => {
                    audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                    preview.src = URL.createObjectURL(audioBlob);
                    
                    try {
                        originalAudioBuffer = await decodeAudio(audioBlob);
                    } catch (err) {
                        console.error('Failed to decode audio:', err);
                    }
                    
                    transformBtn.disabled = false;
                    showStatus('Recording ready! Select an effect and click Transform.', 'ready');
                };
            } catch (err) {
                showStatus('Microphone access denied. Please use localhost:5000', 'recording');
            }
        }
        
        // Record button - click to toggle
        recordBtn.addEventListener('click', toggleRecording);
        
        function toggleRecording() {
            if (!mediaRecorder) return;
            
            if (isRecording) {
                stopRecording();
            } else {
                startRecording();
            }
        }
        
        function startRecording() {
            if (audioContext.state === 'suspended') {
                audioContext.resume();
            }
            
            audioChunks = [];
            mediaRecorder.start();
            isRecording = true;
            recordBtn.classList.add('recording');
            recordBtn.textContent = '⏹️ Click to Stop';
            showStatus('Recording... Click the button to stop.', 'recording');
        }
        
        function stopRecording() {
            if (!mediaRecorder || mediaRecorder.state !== 'recording') return;
            
            mediaRecorder.stop();
            isRecording = false;
            recordBtn.classList.remove('recording');
            recordBtn.textContent = '🎙️ Click to Start Recording';
        }
        
        // Transform button
        transformBtn.addEventListener('click', async () => {
            if (!audioBlob) return;
            
            showStatus('Processing your audio...', 'processing');
            transformBtn.disabled = true;
            
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');
            formData.append('effect', effectSelect.value);
            
            try {
                const response = await fetch('/transform', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    const resultBlob = await response.blob();
                    result.src = URL.createObjectURL(resultBlob);
                    
                    resultSection.classList.add('show');
                    
                    // Draw both waveforms
                    if (originalAudioBuffer) {
                        drawWaveform(document.getElementById('compareOriginal'), originalAudioBuffer, '#e74c3c');
                    }
                    
                    try {
                        const resultBuffer = await decodeAudio(resultBlob);
                        drawWaveform(document.getElementById('compareResult'), resultBuffer, '#667eea');
                    } catch (err) {
                        console.error('Failed to decode result audio:', err);
                    }
                    
                    hideStatus();
                } else {
                    showStatus('Processing failed. Try again.', 'recording');
                }
            } catch (err) {
                showStatus('Error: ' + err.message, 'recording');
            }
            
            transformBtn.disabled = false;
        });
        
        initMicrophone();
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(TEMPLATE)

@app.route("/transform", methods=["POST"])
def transform():
    if "audio" not in request.files:
        return "No audio file provided", 400
    
    file = request.files["audio"]
    effect = request.form.get("effect", "reverse")
    
    if effect not in EFFECTS:
        return "Unknown effect", 400
    
    with tempfile.NamedTemporaryFile(suffix=".webm", delete=False) as tmp_in:
        file.save(tmp_in.name)
        input_path = tmp_in.name
    
    output_path = tempfile.mktemp(suffix=".mp3")
    
    cmd = [
        "ffmpeg", "-y",
        "-i", input_path,
        *EFFECTS[effect],
        output_path
    ]
    
    result = subprocess.run(cmd, capture_output=True)
    os.remove(input_path)
    
    if result.returncode != 0:
        return f"Processing failed: {result.stderr.decode()}", 500
    
    return send_file(
        output_path,
        mimetype="audio/mpeg",
        as_attachment=False,
        download_name=f"voice_{effect}.mp3"
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
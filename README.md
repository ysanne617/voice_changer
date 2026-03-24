# 🎤 Voice Changer

A simple web app that records your voice and applies audio effects using FFmpeg.

Built for the **Python Environment & Docker Workshop** to demonstrate:
- Python dependency management with **uv**
- System dependency management with **Docker**


## Requirements

- Docker installed ([Get Docker](https://docs.docker.com/get-docker/))
- Microphone access in browser

## Quick Start (Docker)

```bash
# Build the image
docker build -t voice-changer .

# Run the container
docker run --name voice-changer -p 5000:5000 voice-changer
```

Open http://localhost:5000 in your browser.

To stop:
```bash
docker stop voice-changer
```
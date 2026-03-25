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

Open http://localhost:5000 in your browser to play with!

```bash
# To stop the container
docker stop voice-changer
```

## Workshop Exercise: Add the "Reverse" Effect

Your task is to add a new audio effect that plays your voice backwards!

### Step 1: Run container in development mode

Use **bind mount** to sync your local code with the container:

```bash
docker run --name voice-changer-dev \
    -p 5000:5000 \
    -v $(pwd)/app.py:/app/app.py \
    voice-changer

# PowerShell: use ${pwd} instead of $(pwd)
docker run --name voice-changer-dev `
    -p 5000:5000 `
    -v ${pwd}/app.py:/app/app.py `
    voice-changer
```
### Step 2: Edit `app.py`

Find the `EFFECTS` dictionary and add the reverse effect

### Step 3: Update the HTML dropdown

Find the `<select id="effect">` in the TEMPLATE and add the new option `Reverse_yourstudentID`

### Step 4: Test your changes
1. Save `app.py`
2. Refresh http://localhost:5000 in your browser
3. Select "Reverse_yourstudentID" and test it!

### Step 5: Save your results for Blackboard submission

Save a `screenshot` (**sample on lecture slides**) showing both:
- The browser with your effect working
- The terminal with docker run command visible

### Step 6: Clean up
```bash
docker stop voice-changer-dev
docker rm voice-changer-dev
docker rm voice-changer
```
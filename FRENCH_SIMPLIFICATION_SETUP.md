# French Simplification App - Setup Guide

This guide explains how to set up and use the French simplification feature for real-time subtitle display during video calls on Mac.

## Overview

The system consists of two components:
1. **WhisperLiveKit Server** - Captures audio, transcribes French speech, and simplifies it in real-time
2. **Subtitle Overlay App** - Displays simplified French subtitles in a floating window

## Prerequisites

- macOS (tested on macOS 10.14+)
- Python 3.9-3.15
- FFmpeg (for audio processing)
- BlackHole or similar virtual audio device (for system audio capture)

## Installation

### 1. Install WhisperLiveKit

```bash
# Clone the repository (if not already done)
cd WhisperLiveKit

# Install dependencies
pip install -e .

# Install additional dependency for French simplification
pip install aiohttp
```

### 2. Install FFmpeg

```bash
brew install ffmpeg
```

### 3. Install BlackHole (for capturing system audio)

BlackHole is a virtual audio device that allows you to route system audio to applications.

```bash
brew install blackhole-2ch
```

**Alternative:** You can also download BlackHole from [https://existential.audio/blackhole/](https://existential.audio/blackhole/)

### 4. Set up API Keys

The French simplification feature requires an API key from OpenAI or Anthropic.

**Option 1: OpenAI (default)**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Option 2: Anthropic**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key-here"
```

You can add these to your `~/.bashrc` or `~/.zshrc` to make them permanent.

## Audio Setup for Video Calls

To capture audio from your video calls (Zoom, Google Meet, etc.), you need to route the audio through BlackHole.

### Option 1: Using BlackHole with Multi-Output Device (Recommended)

This allows you to hear the audio AND capture it:

1. Open **Audio MIDI Setup** (found in `/Applications/Utilities/`)

2. Click the **+** button at the bottom left and select **Create Multi-Output Device**

3. Check both:
   - Your regular output device (e.g., "MacBook Pro Speakers" or headphones)
   - **BlackHole 2ch**

4. Right-click the Multi-Output Device and select **Use This Device For Sound Output**

5. In your video call app (Zoom, Meet, etc.), set the audio output to the **Multi-Output Device**

### Option 2: Using BlackHole Only

1. In **System Preferences** > **Sound** > **Output**, select **BlackHole 2ch**
2. Note: You won't hear the audio yourself with this method

### Configure WhisperLiveKit to Use BlackHole

In **System Preferences** > **Sound** > **Input**, you can see BlackHole as an input device.

You'll configure this when starting the WhisperLiveKit server (see below).

## Usage

### Step 1: Start the WhisperLiveKit Server

```bash
python -m whisperlivekit \
  --simplify-french \
  --simplify-backend openai \
  --model base \
  --lan fr \
  --host localhost \
  --port 8000
```

**Key arguments:**
- `--simplify-french` - Enable French text simplification
- `--simplify-backend openai` - Use OpenAI (or `anthropic`)
- `--model base` - Whisper model size (base is good for real-time performance)
- `--lan fr` - Set language to French
- `--simplify-model gpt-4o-mini` - (Optional) Specify model for simplification
- `--simplify-api-key YOUR_KEY` - (Optional) Provide API key directly

**For faster performance on Apple Silicon:**
```bash
# Install MLX Whisper first
pip install mlx-whisper

# Then run with MLX backend (7x faster on M1/M2/M3)
python -m whisperlivekit \
  --simplify-french \
  --backend mlx-whisper \
  --model base \
  --lan fr
```

### Step 2: Configure Audio Input

When you open the WhisperLiveKit web interface (automatically opens in browser at `http://localhost:8000`), you'll see a microphone selector.

**Select "BlackHole 2ch"** as the input device to capture system audio from your video call.

### Step 3: Start the Subtitle Overlay App

In a new terminal window:

```bash
python french_subtitle_app.py --server-url ws://localhost:8000/asr
```

This will open a transparent overlay window at the bottom of your screen showing:
- **Simplified French** (large, white text) - Easy to read
- **Original French** (smaller, gray text) - For reference

### Step 4: Start Your Video Call

1. Join your video call (Zoom, Google Meet, etc.)
2. Make sure audio output is set to use BlackHole (via Multi-Output Device)
3. As the French speaker talks, you'll see:
   - Real-time transcription in the WhisperLiveKit web interface
   - Simplified French subtitles in the overlay window

## Overlay Window Controls

- **Show original** checkbox - Toggle display of original French text
- **Quit** button - Close the app
- **Keyboard shortcut**: `Cmd+Q` to quit
- The window is **always on top** and **semi-transparent**
- You can drag it to reposition it anywhere on screen

## Customization

### Change Overlay Position

Edit `french_subtitle_app.py` and modify these lines:

```python
# Current: bottom center
x_pos = (screen_width - window_width) // 2
y_pos = screen_height - window_height - 100

# Example: top center
x_pos = (screen_width - window_width) // 2
y_pos = 100

# Example: bottom right
x_pos = screen_width - window_width - 50
y_pos = screen_height - window_height - 100
```

### Change Font Size

Edit `french_subtitle_app.py`:

```python
# For simplified text (currently 18)
subtitle_font = tkfont.Font(family='Helvetica', size=24, weight='bold')

# For original text (currently 12)
font=('Helvetica', 14)
```

### Change Transparency

Edit `french_subtitle_app.py`:

```python
# Current: 0.9 (90% opaque)
self.master.attributes('-alpha', 0.8)  # More transparent
self.master.attributes('-alpha', 1.0)  # Fully opaque
```

### Use Different LLM Backend

```bash
# Use Anthropic instead of OpenAI
export ANTHROPIC_API_KEY="your-anthropic-key"

python -m whisperlivekit \
  --simplify-french \
  --simplify-backend anthropic \
  --simplify-model claude-3-5-haiku-20241022 \
  --model base \
  --lan fr
```

### Simplification Prompt Customization

To change how the text is simplified, edit `whisperlivekit/french_simplifier.py`:

```python
self.system_prompt = """Your custom prompt here..."""
```

For example, you could make it:
- Simpler for language learners (A2-B1 level)
- More formal/informal
- Shorter/longer
- Include explanations of idioms

## Troubleshooting

### "No audio detected"
- Check that BlackHole is selected as the input device in the web interface
- Verify that your video call audio is routed through BlackHole
- Test by playing audio on your Mac and seeing if it's detected

### "API key error"
- Make sure you've set the correct environment variable:
  - `OPENAI_API_KEY` for OpenAI
  - `ANTHROPIC_API_KEY` for Anthropic
- Or pass the key directly with `--simplify-api-key`

### "Simplification is slow"
- Use a faster model: `--simplify-model gpt-4o-mini` (OpenAI)
- Or use `gpt-3.5-turbo` for even faster (but lower quality)
- For Anthropic: `claude-3-5-haiku-20241022` is already the fastest

### "Transcription is laggy"
- Use a smaller Whisper model: `--model tiny` or `--model base`
- On Apple Silicon, use MLX backend: `--backend mlx-whisper`
- Increase chunk size: `--min-chunk-size 0.2`

### "Can't hear audio during call"
- Make sure you created a Multi-Output Device (see Audio Setup above)
- Check that your speakers/headphones are included in the Multi-Output Device

### "Overlay window is in the way"
- Drag it to a different position
- Make it more transparent (edit `french_subtitle_app.py`)
- Resize it by changing `window_width` and `window_height`

## Performance Tips

1. **Use MLX on Apple Silicon**: 7x faster transcription
   ```bash
   pip install mlx-whisper
   --backend mlx-whisper
   ```

2. **Use smaller Whisper model**: `base` or `tiny` for lower latency

3. **Use faster LLM**:
   - OpenAI: `gpt-4o-mini` or `gpt-3.5-turbo`
   - Anthropic: `claude-3-5-haiku-20241022`

4. **Optimize for real-time**:
   ```bash
   python -m whisperlivekit \
     --simplify-french \
     --backend mlx-whisper \
     --model base \
     --lan fr \
     --min-chunk-size 0.1
   ```

## Example Complete Workflow

```bash
# Terminal 1: Start server with French simplification
export OPENAI_API_KEY="sk-..."
python -m whisperlivekit \
  --simplify-french \
  --backend mlx-whisper \
  --model base \
  --lan fr

# Terminal 2: Start subtitle overlay
python french_subtitle_app.py

# Then:
# 1. In browser, select "BlackHole 2ch" as microphone
# 2. Click Record button
# 3. Join your video call
# 4. Watch simplified French appear in real-time!
```

## Architecture

```
Video Call Audio
     ↓
BlackHole (virtual audio device)
     ↓
WhisperLiveKit Server
  ├─ Whisper ASR (transcribes French)
  ├─ LLM API (simplifies French)
  └─ WebSocket (streams results)
     ↓
Subtitle Overlay App
  └─ Displays simplified French subtitles
```

## Credits

- WhisperLiveKit: Real-time speech-to-text framework
- Whisper: OpenAI's speech recognition model
- BlackHole: Virtual audio device for macOS
- French Simplification: Custom integration using OpenAI/Anthropic APIs

## License

Same as WhisperLiveKit parent project.

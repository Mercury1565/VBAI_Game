# VBAIgame

**VBAIgame** is an interactive 3D game built with Pygame and PyOpenGL, featuring a dialogue system powered by OpenAI's API for text-to-speech (TTS) and speech-to-text (STT) using the Whisper model. Players can explore a virtual environment and engage in conversations with NPCs (HR Director and CEO) using voice or text input. The game supports interrupting NPC dialogue with real-time voice recording, creating an immersive experience.

---

## ✨ Features

- **3D Environment**: Navigate a simple 3D world rendered with PyOpenGL.
- **Dialogue System**: Interact with NPCs (Sarah Chen, HR Director, and Michael Chen, CEO) via text or voice.
- **Voice Input**: Record audio by holding the `SPACE` key, with real-time interruption of NPC speech.
- **Text Input**: Type messages and send with `RETURN` when speech mode is disabled.
- **Modular Design**: Organized codebase with separate modules for dialogue, audio, world rendering, and configuration.
- **OpenAI Integration**: Uses OpenAI's TTS and Whisper STT for natural conversation flow.

---

## 📦 Prerequisites

- Python 3.10+
- A valid OpenAI API key
- Microphone for voice input

---

## 🔧 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/VBAIgame.git
cd VBAIgame
```

### 2. Set Up a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure OpenAI API Key

Create a .env file in the VBAIgame directory:

``` bash
OPENAI_API_KEY=your-api-key-here
```
Obtain your API key from OpenAI


## 🚀 Usage
Run the game from the root directory:

``` bash
python -m src.main
```

Or from the src directory (with path fix in main.py):

``` bash
cd src
python main.py
```

## 🎮 Controls

- Movement: W, A, S, D to move, mouse to look around.
- Dialogue:
  - Approach an NPC to start a conversation.
  - Voice Input: Hold SPACE to record, release to send.
  - Text Input: Press M to disable speech mode, type message, press RETURN.
  - Interrupt NPC: Press SPACE or RETURN.
  - Exit Dialogue: Press Shift + Q.
  - Toggle Speech Mode: Press M.

## 📁 Project Structure

```
VBAIgame/
├── src/
│   ├── __init__.py       # Package initialization
│   ├── main.py           # Entry point for the game
│   ├── dialogue.py       # Handles NPC dialogue and player interaction
│   ├── audio_util.py     # Manages audio recording and playback
│   ├── config.py         # Stores game settings and configurations
│   ├── world.py          # Renders the 3D environment
│   ├── player.py         # Implements player movement and camera controls
│   ├── npc.py            # Defines NPC behavior and logic
│   ├── menu.py           # Controls the game menu and options
├── .env                  # Contains the OpenAI API key
├── README.md             # Documentation for the project
```

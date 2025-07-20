import pygame
import numpy as np
import asyncio
import threading
import os
import tempfile
import soundfile as sf
import sounddevice as sd
from audio_util import AudioPlayerAsync, SAMPLE_RATE, CHANNELS
from config import WINDOW_WIDTH, WINDOW_HEIGHT
from OpenGL.GL import *
from pygame.locals import *
import time

class DialogueSystem:
    def __init__(self, client, screen):
        self.client = client
        self.screen = screen
        self.active = False
        self.user_input = ""
        pygame.font.init()
        self.font = pygame.font.Font(None, 24)
        self.npc_message = ""
        self.input_active = False
        self.conversation_history = []
        self.ui_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.SRCALPHA).convert_alpha()
        self.ui_texture = glGenTextures(1)
        self.current_npc = None
        self.initial_player_pos = None
        self.speech_mode = False
        self.audio_player = AudioPlayerAsync()
        self.loop = asyncio.new_event_loop()
        self.loop_thread = threading.Thread(target=self.run_asyncio_loop, daemon=True)
        self.loop_thread.start()
        self.audio_buffer = []
        self.recording = False
        self.is_recording_key_held = False
        devices = sd.query_devices()

        # Identify default input device
        self.default_input_device = None
        for i, device in enumerate(devices):
            if device['max_input_channels'] > 0:
                if i == sd.default.device[0]:  # Check if it's the default input device
                    self.default_input_device = i
                    break
        print(f"[DialogueSystem] Selected default input device: {self.default_input_device}")

    def run_asyncio_loop(self):
        asyncio.set_event_loop(self.loop)
        print("[DialogueSystem] Asyncio loop started")
        self.loop.run_forever()

    async def record_mic_audio(self):
        print("[DialogueSystem] Starting audio recording...")
        read_size = int(SAMPLE_RATE * 0.2)
        stream = None
        try:
            # Use the default input device, fallback to device 0 if not set
            device = self.default_input_device if self.default_input_device is not None else 0
            print(f"[DialogueSystem] Using input device: {device}")
            stream = sd.InputStream(
                device=device,
                channels=CHANNELS,
                samplerate=SAMPLE_RATE,
                dtype="int16",
                blocksize=read_size,
                latency="low"
            )
            await asyncio.sleep(0.5)
            stream.start()
            print("[DialogueSystem] Audio input stream started")
            self.audio_buffer = []
            self.recording = True
            start_time = time.time()
            while self.active and self.speech_mode and self.recording and self.is_recording_key_held:
                if time.time() - start_time > 10:
                    print("[DialogueSystem] Recording timeout reached")
                    break
                if stream.read_available >= read_size:
                    data, overflowed = stream.read(read_size)
                    if overflowed:
                        print("[DialogueSystem] Audio buffer overflow detected")
                    if data.size > 0:
                        self.audio_buffer.append(data)
                        print(f"[DialogueSystem] Recorded audio chunk: {len(data)} samples, max amplitude: {np.max(np.abs(data))}")
                    else:
                        print("[DialogueSystem] No audio data captured in chunk")
                await asyncio.sleep(0.01)
        except Exception as e:
            print(f"[DialogueSystem] Audio input error: {e}")
            self.npc_message = f"Audio input error: {str(e)}. Please check your microphone."
            self.generate_tts(self.npc_message)
        finally:
            if stream is not None:
                stream.stop()
                stream.close()
            self.recording = False
            print("[DialogueSystem] Audio input stream stopped")

    async def process_audio_input(self):
        if not self.audio_buffer:
            print("[DialogueSystem] No audio data to process")
            self.npc_message = "No audio detected. Please hold SPACE to record and release to send."
            self.generate_tts(self.npc_message)
            return
        try:
            audio_data = np.concatenate(self.audio_buffer)
            print(f"[DialogueSystem] Total audio samples: {len(audio_data)}, max amplitude: {np.max(np.abs(audio_data))}")
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                sf.write(temp_file.name, audio_data, SAMPLE_RATE, format='WAV', subtype='PCM_16')
                temp_file_path = temp_file.name
            print(f"[DialogueSystem] Audio saved to temporary file: {temp_file_path}")
            with open(temp_file_path, 'rb') as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            os.unlink(temp_file_path)
            if transcript.strip():
                print(f"[DialogueSystem] Transcribed audio: {transcript}")
                self.conversation_history.append({"role": "user", "content": transcript.strip()})
                self.send_text_message(transcript.strip())
            else:
                print("[DialogueSystem] No speech detected in audio")
                self.npc_message = "I didn't catch that. Could you repeat?"
                self.generate_tts(self.npc_message)
            self.audio_buffer = []
        except Exception as e:
            print(f"[DialogueSystem] Audio transcription error: {e}")
            self.npc_message = f"Sorry, I couldn't process your audio: {str(e)}. Try typing instead."
            self.generate_tts(self.npc_message)
            self.audio_buffer = []

    def generate_tts(self, text):
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice="alloy" if self.current_npc == "HR" else "echo",
                input=text,
                response_format="pcm"
            )
            audio_data = response.read()
            print(f"[DialogueSystem] Generated TTS: {len(audio_data)} bytes")
            self.audio_player.add_data(audio_data)
        except Exception as e:
            print(f"[DialogueSystem] TTS error: {e}")
            self.npc_message = "Audio unavailable, please use text input."

    def start_conversation(self, npc_role="HR", player_pos=None):
        self.active = True
        self.input_active = True
        self.speech_mode = True
        self.current_npc = npc_role
        self.initial_player_pos = [player_pos[0], player_pos[1], player_pos[2]] if player_pos else [0, 0.5, 0]
        print(f"[DialogueSystem] Dialogue started with {npc_role}")

        if self.audio_player:
            self.audio_player.stop()
            self.audio_player.reset_frame_count()

        base_prompt = """Interaction Framework:
            - Maintain consistent personality throughout conversation
            - Remember previous context within the dialogue
            - Use natural speech patterns with occasional filler words
            - Show emotional intelligence in responses
            - Keep responses concise but meaningful (2-3 sentences)
            - React appropriately to both positive and negative interactions
            - If interrupted, acknowledge the interruption briefly and respond to the new input
        """
        if npc_role == "HR":
            system_prompt = f"""{base_prompt}
                You are Sarah Chen, HR Director at Venture Builder AI. Core traits:
                PERSONALITY:
                - Warm but professional demeanor
                - Excellent emotional intelligence
                - Strong ethical boundaries
                - Protective of confidential information
                - Quick to offer practical solutions
                SPEAKING STYLE:
                - Uses supportive language: "I understand that..." "Let's explore..."
                - References policies with context: "According to our wellness policy..."
                - Balances empathy with professionalism
                - On interruption: "Oh, I see you have something new to share. What's on your mind?"
                VOICE: Warm, approachable tone (alloy voice)"""
        else:
            system_prompt = f"""{base_prompt}
                You are Michael Chen, CEO of Venture Builder AI. Core traits:
                PERSONALITY:
                - Visionary yet approachable
                - Strategic thinker
                - Passionate about venture building
                SPEAKING STYLE:
                - Uses storytelling: "When we launched our first venture..."
                - References data: "Our portfolio metrics show..."
                - Balances optimism with realism
                - On interruption: "Hold on, let's pivot to your new question. What's up?"
                VOICE: Authoritative, confident tone (echo voice)"""

        self.conversation_history = [{"role": "system", "content": system_prompt}]
        initial_message = {
            "HR": "Hello there, I am Sarah Chen, HR Director at Venture Builder AI. How can I assist you today?",
            "CEO": "Hello there, I am Michael Chen, CEO at Venture Builder AI. What can I do for you today?"
        }
        self.npc_message = initial_message[npc_role]
        self.conversation_history.append({"role": "assistant", "content": self.npc_message})
        print(f"[DialogueSystem] Initial NPC message: {self.npc_message}")
        self.generate_tts(self.npc_message)

    def send_text_message(self, user_message=None):
        if not self.conversation_history:
            print("[DialogueSystem] No conversation history to send.")
            return
        if user_message:
            self.conversation_history.append({"role": "user", "content": user_message})
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=self.conversation_history,
                temperature=0.85,
                max_tokens=150,
                response_format={"type": "text"},
                top_p=0.95,
                frequency_penalty=0.2,
                presence_penalty=0.1
            )
            ai_message = response.choices[0].message.content
            self.conversation_history.append({"role": "assistant", "content": ai_message})
            self.npc_message = ai_message
            print(f"[DialogueSystem] NPC says: {ai_message}")
            self.generate_tts(ai_message)
        except Exception as e:
            self.npc_message = "I apologize, but I'm having trouble connecting right now."
            print(f"[DialogueSystem] Text error: {e}")
            self.generate_tts(self.npc_message)

    def handle_input(self, event):
        if not self.active:
            return
        if event.type == pygame.KEYDOWN:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LSHIFT] and event.key == pygame.K_q:
                self.active = False
                self.input_active = False
                self.speech_mode = False
                self.recording = False
                self.is_recording_key_held = False
                self.audio_player.stop()
                print("[DialogueSystem] Chat ended")
                return {"command": "move_player_back", "position": self.initial_player_pos}
            if event.key == pygame.K_m:
                self.speech_mode = not self.speech_mode
                if not self.speech_mode:
                    self.recording = False
                    self.is_recording_key_held = False
                print(f"[DialogueSystem] Speech mode {'enabled' if self.speech_mode else 'disabled'}")
            if event.key == pygame.K_SPACE and self.speech_mode and not self.recording:
                self.audio_player.stop()
                self.audio_player.reset_frame_count()
                print("[DialogueSystem] Stopped NPC audio for new recording")
                self.is_recording_key_held = True
                self.recording = True
                asyncio.run_coroutine_threadsafe(self.record_mic_audio(), self.loop)
                print("[DialogueSystem] Started recording (SPACE held)")
            if event.key == pygame.K_RETURN:
                if self.speech_mode:
                    pass
                elif self.user_input.strip():
                    self.audio_player.stop()
                    self.audio_player.reset_frame_count()
                    print("[DialogueSystem] Stopped NPC audio for new text input")
                    print(f"[DialogueSystem] User said: {self.user_input}")
                    self.send_text_message(self.user_input.strip())
                    self.user_input = ""
            elif event.key == pygame.K_BACKSPACE:
                self.user_input = self.user_input[:-1]
            elif event.unicode.isprintable():
                self.user_input += event.unicode
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE and self.speech_mode and self.recording:
                print("[DialogueSystem] SPACE key released, stopping recording")
                self.is_recording_key_held = False
                self.recording = False
                asyncio.run_coroutine_threadsafe(self.process_audio_input(), self.loop)
                print("[DialogueSystem] Stopped recording and processing audio (SPACE released)")

    def render_text(self, surface, text, x, y):
        max_width = WINDOW_WIDTH - 40
        line_height = 25
        words = text.split()
        lines = []
        current_line = []
        current_width = 0
        text_color = (255, 255, 255)
        for word in words:
            word_surface = self.font.render(word + ' ', True, text_color)
            word_width = word_surface.get_width()
            if current_width + word_width <= max_width:
                current_line.append(word)
                current_width += word_width
            else:
                lines.append(' '.join(current_line))
                current_line = [word]
                current_width = word_width
        if current_line:
            lines.append(' '.join(current_line))
        for i, line in enumerate(lines):
            text_surface = self.font.render(line, True, text_color)
            surface.blit(text_surface, (x, y + i * line_height))
        return len(lines) * line_height

    def render(self):
        if not self.active:
            return
        self.ui_surface.fill((0, 0, 0, 0))
        box_height = 200
        box_y = WINDOW_HEIGHT - box_height - 20
        box_color = (0, 0, 0, 230)
        pygame.draw.rect(self.ui_surface, box_color, (20, box_y, WINDOW_WIDTH - 40, box_height))
        pygame.draw.rect(self.ui_surface, (255, 255, 255, 255), (20, box_y, WINDOW_WIDTH - 40, box_height), 2)
        instruction_text = "Hold SPACE to record, release to send, M to toggle mic, Shift+Q to exit"
        quit_text_surface = self.font.render(instruction_text, True, (255, 255, 255))
        self.ui_surface.blit(quit_text_surface, (40, box_y + 10))
        if self.npc_message:
            self.render_text(self.ui_surface, self.npc_message, 40, box_y + 40)
        if self.input_active:
            input_prompt = "> " + self.user_input + "_" if not self.speech_mode else "> (Recording...)" if self.recording else "> (Hold SPACE to record)"
            input_surface = self.font.render(input_prompt, True, (255, 255, 255))
            self.ui_surface.blit(input_surface, (40, box_y + box_height - 40))
        texture_data = pygame.image.tostring(self.ui_surface, "RGBA", True)
        glPushAttrib(GL_ALL_ATTRIB_BITS)
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WINDOW_WIDTH, 0, WINDOW_HEIGHT, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, self.ui_texture)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, WINDOW_WIDTH, WINDOW_HEIGHT, 0, GL_RGBA, GL_UNSIGNED_BYTE, texture_data)
        glBegin(GL_QUADS)
        glTexCoord2f(0, 0); glVertex2f(0, 0)
        glTexCoord2f(1, 0); glVertex2f(WINDOW_WIDTH, 0)
        glTexCoord2f(1, 1); glVertex2f(WINDOW_WIDTH, WINDOW_HEIGHT)
        glTexCoord2f(0, 1); glVertex2f(0, WINDOW_HEIGHT)
        glEnd()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
        glPopAttrib()

    def __del__(self):
        self.audio_player.terminate()
        if self.loop:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.loop_thread.join()
import os
import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import sys
from dotenv import load_dotenv
from openai import OpenAI
from dialogue import DialogueSystem
from world import World
from player import Player
from npc import NPC
from menu import MenuScreen
from config import *
import time
import math

# Load environment variables
load_dotenv()
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    print("[OpenAI] API key not found. Please set OPENAI_API_KEY in your .env file.")
    sys.exit(1)
client = OpenAI(api_key=api_key)
print("[OpenAI] API key loaded successfully.")

# Initialize Pygame
pygame.init()
try:
    pygame.mixer.init(frequency=44100, size=-16, channels=1, buffer=4096)
except Exception as e:
    print(f"[Pygame] Mixer initialization error: {e}")
display = (WINDOW_WIDTH, WINDOW_HEIGHT)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 2)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
screen = pygame.display.get_surface()

# Set up the camera and perspective
glEnable(GL_DEPTH_TEST)
glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(45, (display[0] / display[1]), 0.1, 50.0)
glMatrixMode(GL_MODELVIEW)

# Set up basic lighting
glEnable(GL_LIGHTING)
glEnable(GL_LIGHT0)
glLightfv(GL_LIGHT0, GL_POSITION, [0, 5, 5, 1])
glLightfv(GL_LIGHT0, GL_AMBIENT, [0.5, 0.5, 0.5, 1])
glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1])

# Enable blending for transparency
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# Initial camera position
glTranslatef(0.0, 0.0, -5)

class Game3D:
    def __init__(self):
        self.menu = MenuScreen(screen)
        self.player = Player()
        self.world = World()
        self.dialogue = DialogueSystem(client, screen)
        self.hr_npc = NPC(-3.3, 0, -2, "HR")
        self.ceo_npc = NPC(3.3, 0, 1, "CEO")
        self.interaction_distance = 2.0
        self.last_interaction_time = 0

    def move_player_away_from_npc(self, npc_pos):
        dx = self.player.pos[0] - npc_pos[0]
        dz = self.player.pos[2] - npc_pos[2]
        distance = math.sqrt(dx * dx + dz * dz)
        if distance > 0:
            dx /= distance
            dz /= distance
            self.player.pos[0] = npc_pos[0] + (dx * 3)
            self.player.pos[2] = npc_pos[2] + (dz * 3)

    def run(self):
        running = True
        while running:
            if self.menu.active:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_RETURN and time.time() - self.menu.start_time > (len(TITLE) / 15 + 1):
                            self.menu.active = False
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                self.menu.render()
            else:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                    elif event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                        if event.key == pygame.K_ESCAPE and event.type == pygame.KEYDOWN:
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                            running = False
                        if self.dialogue.active:
                            result = self.dialogue.handle_input(event)
                            if isinstance(result, dict) and result.get("command") == "move_player_back":
                                current_npc = self.hr_npc if self.dialogue.current_npc == "HR" else self.ceo_npc
                                self.move_player_away_from_npc(current_npc.pos)
                    elif event.type == pygame.MOUSEMOTION:
                        x, y = event.rel
                        self.player.update_rotation(x, y)
                if not self.dialogue.active:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_w]: self.player.move(0, -1)
                    if keys[pygame.K_s]: self.player.move(0, 1)
                    if keys[pygame.K_a]: self.player.move(-1, 0)
                    if keys[pygame.K_d]: self.player.move(1, 0)
                current_time = time.time()
                if current_time - self.last_interaction_time > 0.5:
                    dx = self.player.pos[0] - self.hr_npc.pos[0]
                    dz = self.player.pos[2] - self.hr_npc.pos[2]
                    hr_distance = math.sqrt(dx * dx + dz * dz)
                    dx = self.player.pos[0] - self.ceo_npc.pos[0]
                    dz = self.player.pos[2] - self.ceo_npc.pos[2]
                    ceo_distance = math.sqrt(dx * dx + dz * dz)
                    if hr_distance < self.interaction_distance and not self.dialogue.active:
                        self.dialogue.start_conversation("HR", self.player.pos)
                        self.last_interaction_time = current_time
                    elif ceo_distance < self.interaction_distance and not self.dialogue.active:
                        self.dialogue.start_conversation("CEO", self.player.pos)
                        self.last_interaction_time = current_time
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                glPushMatrix()
                glRotatef(self.player.rot[0], 1, 0, 0)
                glRotatef(self.player.rot[1], 0, 1, 0)
                glTranslatef(-self.player.pos[0], -self.player.pos[1], -self.player.pos[2])
                self.world.draw()
                self.hr_npc.draw()
                self.ceo_npc.draw()
                glPopMatrix()
                self.dialogue.render()
                pygame.display.flip()
                pygame.time.Clock().tick(FPS)
        pygame.quit()

# Create and run game
if __name__ == "__main__":
    game = Game3D()
    game.run()
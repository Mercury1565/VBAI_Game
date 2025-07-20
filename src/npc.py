from OpenGL.GL import *
from world import draw_sphere, draw_cube

class NPC:
    def __init__(self, x, y, z, role="HR"):
        self.scale = 0.6
        self.pos = [x, 0.65, z]
        self.size = 0.5
        self.role = role
        self.skin_color = (0.8, 0.7, 0.6)
        self.hair_color = (0.2, 0.15, 0.1) if role == "HR" else (0.3, 0.3, 0.3)
        if role == "HR":
            self.clothes_primary = (0.8, 0.2, 0.2)
            self.clothes_secondary = (0.6, 0.15, 0.15)
        else:
            self.clothes_primary = (0.2, 0.3, 0.8)
            self.clothes_secondary = (0.15, 0.2, 0.6)

    def draw(self):
        glPushMatrix()
        glTranslatef(self.pos[0], self.pos[1], self.pos[2])
        glScalef(self.scale, self.scale, self.scale)
        glColor3f(*self.skin_color)
        draw_sphere(0.12, 16, 16)
        glColor3f(*self.hair_color)
        glPushMatrix()
        glTranslatef(0, 0.05, 0)
        draw_sphere(0.13, 16, 16)
        glPopMatrix()
        glColor3f(*self.clothes_primary)
        glPushMatrix()
        glTranslatef(0, -0.3, 0)
        glScalef(0.3, 0.4, 0.2)
        draw_cube()
        glPopMatrix()
        glColor3f(*self.clothes_secondary)
        for x_offset in [-0.2, 0.2]:
            glPushMatrix()
            glTranslatef(x_offset, -0.3, 0)
            glScalef(0.1, 0.4, 0.1)
            draw_cube()
            glPopMatrix()
        for x_offset in [-0.1, 0.1]:
            glPushMatrix()
            glTranslatef(x_offset, -0.8, 0)
            glScalef(0.1, 0.5, 0.1)
            draw_cube()
            glPopMatrix()
        glPopMatrix()
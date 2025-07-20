import math

class Player:
    def __init__(self):
        self.pos = [0, 0.5, 0]
        self.rot = [0, 0, 0]
        self.speed = 0.3
        self.mouse_sensitivity = 0.5

    def move(self, dx, dz):
        angle = math.radians(-self.rot[1])
        move_x = (dx * math.cos(angle) + dz * math.sin(angle)) * self.speed
        move_z = (-dx * math.sin(angle) + dz * math.cos(angle)) * self.speed
        new_x = self.pos[0] + move_x
        new_z = self.pos[2] + move_z
        room_limit = 4.5
        if abs(new_x) < room_limit:
            self.pos[0] = new_x
        if abs(new_z) < room_limit:
            self.pos[2] = new_z

    def update_rotation(self, dx, dy):
        self.rot[1] += dx * self.mouse_sensitivity
import asyncio
import platform
import pygame
from random import randint, uniform, choice, gauss
import math
import colorsys
from PIL import Image, ImageDraw, ImageFont

vector2 = pygame.math.Vector2
trails = []
fade_particles = []
smoke_particles = []

# General settings
GRAVITY_FIREWORK = vector2(0, 0.25)
GRAVITY_PARTICLE = vector2(0, 0.05)
DISPLAY_WIDTH = 1500
DISPLAY_HEIGHT = 1000
BACKGROUND_COLOR = (15, 15, 25)
FPS = 60

# Firework settings
FIREWORK_SPEED_MIN = 16
FIREWORK_SPEED_MAX = 20
FIREWORK_SIZE = 5

# Particle settings
PARTICLE_LIFESPAN = 150
X_SPREAD = 0.95
Y_SPREAD = 0.95
PARTICLE_SIZE_MIN = 1
PARTICLE_SIZE_MAX = 4
MIN_PARTICLES = 300
MAX_PARTICLES = 450
X_WIGGLE_SCALE = 25
Y_WIGGLE_SCALE = 15
EXPLOSION_RADIUS_MIN = 35
EXPLOSION_RADIUS_MAX = 50
COLORFUL = True
GLOW_INTENSITY = 0.7

# Trail settings
TRAIL_LIFESPAN = PARTICLE_LIFESPAN / 2.5
TRAIL_FREQUENCY = 8
TRAILS = True
SMOKE_ENABLED = True

# Font settings
FONT_PATH = "/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf"
CHARACTER = " Happy Every Day!"
places = [i for i in range(100, 1400, 250)]
place = 0

def get_char_contour_points(font_path, char, size):
    font = ImageFont.truetype(font_path, size)
    image = Image.new("L", (size * 2, size * 2), 0)
    draw = ImageDraw.Draw(image)
    draw.text((0, 0), char, font=font, fill=255)
    points = []
    for y in range(image.height):
        for x in range(image.width):
            if image.getpixel((x, y)) > 128:
                points.append((x, y))
    return [(x - 0.25 * size, y - 0.85 * size) for x, y in points]

def generate_vivid_color():
    hue = uniform(0, 1)
    saturation = uniform(0.85, 1.0)
    value = uniform(0.8, 1.0)
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
    return (int(r * 255), int(g * 255), int(b * 255))

def create_glow_color(base_color, intensity):
    return tuple(min(int(c * intensity + 255 * (1 - intensity)), 255) for c in base_color)

class Firework:
    def __init__(self, character: str):
        self.colour = generate_vivid_color()
        self.colours = [generate_vivid_color() for _ in range(3)]
        self.explosion_type = choice(['burst', 'sparkler', 'twinkle'])
        if place == 0:
            self.firework = Particle(randint(0, DISPLAY_WIDTH), DISPLAY_HEIGHT, 0, 0, 0, True, self.colour)
        else:
            self.firework = Particle(places[place], DISPLAY_HEIGHT, 0, 0, 0, True, self.colour)
        self.exploded = False
        self.particles = []
        self.char = bool(character)
        self.points = get_char_contour_points(FONT_PATH, character, 50) if self.char else []

    def update(self, win: pygame.Surface) -> None:
        if not self.exploded:
            self.firework.apply_force(GRAVITY_FIREWORK)
            self.firework.move()
            self.show(win)
            if self.firework.vel.y >= 0:
                self.exploded = True
                self.explode()
        else:
            for particle in self.particles:
                particle.update()
                particle.show(win)

    def explode(self):
        num_particles = randint(MIN_PARTICLES, MAX_PARTICLES)
        if self.char:
            for dx, dy in self.points:
                colour = choice(self.colours) if COLORFUL else self.colour
                r = math.sqrt(dx**2 + dy**2)
                particle = Particle(self.firework.pos.x, self.firework.pos.y, dx, dy, r, False, colour, self.explosion_type)
                self.particles.append(particle)
        else:
            for _ in range(num_particles):
                colour = choice(self.colours) if COLORFUL else self.colour
                particle = Particle(self.firework.pos.x, self.firework.pos.y, 0, 0, 0, False, colour, self.explosion_type)
                self.particles.append(particle)

    def show(self, win: pygame.Surface) -> None:
        x, y = int(self.firework.pos.x), int(self.firework.pos.y)
        glow_color = create_glow_color(self.colour, GLOW_INTENSITY)
        pygame.draw.circle(win, glow_color, (x, y), self.firework.size + 2)
        pygame.draw.circle(win, self.colour, (x, y), self.firework.size)

    def remove(self) -> bool:
        if not self.exploded:
            return False
        for p in self.particles[:]:
            if p.remove:
                self.particles.remove(p)
        return len(self.particles) == 0

class Particle:
    def __init__(self, x, y, dx, dy, r, firework, colour, explosion_type='burst'):
        self.firework = firework
        self.pos = vector2(x, y)
        self.origin = vector2(x, y)
        self.acc = vector2(0, 0)
        self.remove = False
        self.explosion_type = explosion_type
        self.colour = colour
        self.glow_colour = create_glow_color(colour, GLOW_INTENSITY)
        self.explosion_radius = r if r else randint(EXPLOSION_RADIUS_MIN, EXPLOSION_RADIUS_MAX)
        self.life = 0
        self.trail_frequency = TRAIL_FREQUENCY + randint(-2, 2)
        
        if self.firework:
            self.vel = vector2(0, -randint(FIREWORK_SPEED_MIN, FIREWORK_SPEED_MAX))
            self.size = FIREWORK_SIZE
        else:
            if dx == 0 and dy == 0:
                angle = uniform(0, 2 * math.pi)
                speed = gauss(self.explosion_radius * 0.1, self.explosion_radius * 0.05)
                self.vel = vector2(math.cos(angle) * speed, math.sin(angle) * speed)
                if self.explosion_type == 'sparkler':
                    self.vel *= uniform(1.2, 1.5)
                elif self.explosion_type == 'twinkle':
                    self.vel *= uniform(0.5, 0.8)
            else:
                self.vel = vector2(0.7 * dx, 0.7 * dy)
            self.size = randint(PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX)
            self.move()
            self.outside_spawn_radius()

    def update(self) -> None:
        self.life += 1
        if self.life % self.trail_frequency == 0:
            trails.append(Trail(self.pos.x, self.pos.y, False, self.colour, self.size))
            if SMOKE_ENABLED and randint(0, 5) == 0:
                smoke_particles.append(Smoke(self.pos.x, self.pos.y, self.size))
        
        if self.explosion_type == 'twinkle' and randint(0, 20) == 0:
            self.size = randint(PARTICLE_SIZE_MIN, PARTICLE_SIZE_MAX + 2)
        
        force = vector2(
            uniform(-1, 1) / X_WIGGLE_SCALE,
            GRAVITY_PARTICLE.y + uniform(-1, 1) / Y_WIGGLE_SCALE
        )
        self.apply_force(force)
        self.move()

    def apply_force(self, force: vector2) -> None:
        self.acc += force

    def outside_spawn_radius(self) -> bool:
        distance = math.sqrt((self.pos.x - self.origin.x) ** 2 + (self.pos.y - self.origin.y) ** 2)
        return distance > self.explosion_radius

    def move(self) -> None:
        if not self.firework:
            self.vel.x *= X_SPREAD
            self.vel.y *= Y_SPREAD
        self.vel += self.acc
        self.pos += self.vel
        self.acc *= 0
        self.decay()

    def show(self, win: pygame.Surface) -> None:
        x, y = int(self.pos.x), int(self.pos.y)
        alpha = max(0, 1 - self.life / PARTICLE_LIFESPAN)
        glow_size = self.size + 2 if self.explosion_type != 'twinkle' else self.size + 4
        glow_color = tuple(int(c * alpha) for c in self.glow_colour)
        pygame.draw.circle(win, glow_color, (x, y), glow_size)
        pygame.draw.circle(win, tuple(int(c * alpha) for c in self.colour), (x, y), self.size)

    def decay(self) -> None:
        if self.life > PARTICLE_LIFESPAN:
            if randint(0, 10) == 0:
                self.remove = True
        if self.life > PARTICLE_LIFESPAN * 1.5:
            self.remove = True

class Trail(Particle):
    def __init__(self, x, y, is_firework, colour, parent_size):
        Particle.__init__(self, x, y, 0, 0, 0, is_firework, colour)
        self.size = max(1, parent_size - 1)
        self.glow_colour = create_glow_color(colour, GLOW_INTENSITY)

    def decay(self) -> bool:
        self.life += 1
        if self.life % 50 == 0:
            self.size = max(0, self.size - 1)
        alpha = max(0, 1 - self.life / TRAIL_LIFESPAN)
        self.colour = tuple(int(c * alpha) for c in self.colour)
        if self.life > TRAIL_LIFESPAN and randint(0, 10) == 0:
            return True
        if self.life > TRAIL_LIFESPAN * 1.2:
            return True
        return False

    def show(self, win: pygame.Surface) -> None:
        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.circle(win, self.glow_colour, (x, y), self.size + 1)
        pygame.draw.circle(win, self.colour, (x, y), self.size)

class Smoke:
    def __init__(self, x, y, size):
        self.pos = vector2(x, y)
        self.life = 0
        self.size = size
        self.colour = (100, 100, 120)
        self.remove = False

    def update(self):
        self.life += 1
        self.pos += vector2(uniform(-0.5, 0.5), uniform(-0.3, 0.3))
        self.size += 0.1
        alpha = max(0, 1 - self.life / (TRAIL_LIFESPAN * 1.5))
        self.colour = tuple(int(c * alpha) for c in self.colour)
        if self.life > TRAIL_LIFESPAN * 1.5:
            self.remove = True

    def show(self, win: pygame.Surface):
        x, y = int(self.pos.x), int(self.pos.y)
        pygame.draw.circle(win, self.colour, (x, y), int(self.size))

def update(win: pygame.Surface, fireworks: list, trails: list, smoke_particles: list) -> None:
    if TRAILS:
        for t in trails[:]:
            t.show(win)
            if t.decay():
                trails.remove(t)
    if SMOKE_ENABLED:
        for s in smoke_particles[:]:
            s.update()
            s.show(win)
            if s.remove:
                smoke_particles.remove(s)
    for fw in fireworks[:]:
        fw.update(win)
        if fw.remove():
            fireworks.remove(fw)
    pygame.display.update()

async def main():
    pygame.init()
    pygame.display.set_caption("Spectacular Fireworks")
    win = pygame.display.set_mode((DISPLAY_WIDTH, DISPLAY_HEIGHT))
    clock = pygame.time.Clock()
    global place
    fireworks = []
    index = 0
    is_paused = False
    pause_start_time = 0

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return

        clock.tick(FPS)
        win.fill(BACKGROUND_COLOR)

        if not is_paused:
            if index < len(CHARACTER):
                current_char = CHARACTER[index]
                if current_char == " ":
                    is_paused = True
                    pause_start_time = pygame.time.get_ticks()
                    place = 0
                else:
                    place = (place + 1) % len(places)
                fireworks.append(Firework(current_char))
                index += 1
            else:
                if randint(0, 50) == 1:
                    place = 0
                    fireworks.append(Firework(""))
        else:
            current_time = pygame.time.get_ticks()
            if current_time - pause_start_time >= 3000:
                is_paused = False

            update(win, fireworks, trails, smoke_particles)
        await asyncio.sleep(1.0 / FPS)

if platform.system() == "Emscripten":
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        asyncio.run(main())
"""
Visual effects and animation system for Cake Sort Puzzle.
Includes particles, animations, and cake decorations.
"""

import pygame
import random
import math
import time

class ParticleSystem:
    def __init__(self):
        self.particles = []
    
    def add_particle(self, particle_type, x, y, color=None, **kwargs):
        """Add a new particle to the system"""
        if particle_type == 'selection':
            self.particles.append({
                'type': 'selection',
                'x': x,
                'y': y,
                'radius': 5,
                'life': 0.5,
                'start_time': time.time(),
                'color': color or (255, 255, 0, 200)
            })
        elif particle_type == 'move':
            for _ in range(5):
                self.particles.append({
                    'type': 'move',
                    'x': x + (random.random() - 0.5) * 30,
                    'y': y + (random.random() - 0.5) * 30,
                    'vx': (random.random() - 0.5) * 2,
                    'vy': -random.random() * 2,
                    'radius': random.random() * 3 + 2,
                    'life': random.random() * 0.5 + 0.5,
                    'start_time': time.time(),
                    'color': color or (255, 255, 255, 200)
                })
        elif particle_type == 'confetti':
            colors = [(255,0,0), (0,255,0), (0,0,255), (255,255,0), (255,0,255), (0,255,255)]
            self.particles.append({
                'type': 'confetti',
                'x': x + (random.random() - 0.5) * 200,
                'y': y + (random.random() - 0.5) * 100,
                'vx': (random.random() - 0.5) * 3,
                'vy': random.random() * 2 + 1,
                'size': random.random() * 5 + 5,
                'life': random.random() * 2 + 1,
                'start_time': time.time(),
                'color': color or random.choice(colors)
            })
        elif particle_type == 'sparkle':
            self.particles.append({
                'type': 'sparkle',
                'x': x,
                'y': y,
                'size': random.random() * 3 + 2,
                'life': random.random() * 0.5 + 0.5,
                'start_time': time.time(),
                'color': color or (255, 255, 200, 200)
            })
    
    def update(self):
        """Update all particles and remove expired ones"""
        current_time = time.time()
        remaining_particles = []
        
        for particle in self.particles:
            age = current_time - particle['start_time']
            if age < particle['life']:
                # Update particle position if it has velocity
                if 'vx' in particle:
                    particle['x'] += particle['vx']
                    particle['y'] += particle['vy']
                    if particle['type'] == 'confetti':
                        particle['vy'] += 0.1  # Gravity
                
                remaining_particles.append(particle)
        
        self.particles = remaining_particles
    
    def draw(self, surface):
        """Draw all active particles"""
        current_time = time.time()
        
        for particle in self.particles:
            age = current_time - particle['start_time']
            life_ratio = 1 - (age / particle['life'])
            
            if particle['type'] == 'selection':
                radius = particle['radius'] * (1 + (1 - life_ratio) * 2)
                color = list(particle['color'])
                color[3] = int(color[3] * life_ratio)
                pygame.draw.circle(
                    surface,
                    color,
                    (int(particle['x']), int(particle['y'])),
                    int(radius),
                    1
                )
            elif particle['type'] == 'move':
                radius = particle['radius'] * life_ratio
                color = list(particle['color'])
                color[3] = int(color[3] * life_ratio)
                pygame.draw.circle(
                    surface,
                    color,
                    (int(particle['x']), int(particle['y'])),
                    int(radius)
                )
            elif particle['type'] == 'confetti':
                size = particle['size']
                # Use RGBA only if the surface has per-pixel alpha
                if surface.get_flags() & pygame.SRCALPHA:
                    color = particle['color'] + (int(255 * life_ratio),)
                else:
                    # For surfaces without alpha
                    color = particle['color']
                pygame.draw.rect(
                    surface,
                    color,
                    pygame.Rect(
                        int(particle['x'] - size/2),
                        int(particle['y'] - size/2),
                        int(size),
                        int(size)
                    )
                )
            elif particle['type'] == 'sparkle':
                size = particle['size'] * life_ratio * 2
                if surface.get_flags() & pygame.SRCALPHA:
                    color = particle['color'][:3] + (int(particle['color'][3] * life_ratio),)
                else:
                    color = particle['color'][:3]
                pygame.draw.circle(
                    surface,
                    color,
                    (int(particle['x']), int(particle['y'])),
                    int(size)
                )

def draw_cake_decoration(surface, decoration_type, rect, color):
    """Draw decorations on cake layers"""
    if decoration_type == 'sprinkles':
        for _ in range(10):
            x = rect.x + random.randint(5, rect.width - 5)
            y = rect.y + random.randint(5, rect.height - 5)
            pygame.draw.line(
                surface, 
                color,
                (x, y), 
                (x + random.randint(-3, 3), y + random.randint(-3, 3)),
                2
            )
    
    elif decoration_type == 'dots':
        for _ in range(5):
            x = rect.x + random.randint(10, rect.width - 10)
            y = rect.y + random.randint(5, rect.height - 5)
            pygame.draw.circle(
                surface,
                color,
                (x, y),
                2
            )
    
    elif decoration_type == 'swirl':
        center_x = rect.x + rect.width // 2
        center_y = rect.y + rect.height // 2
        radius = min(rect.width, rect.height) // 4
        points = []
        
        for i in range(12):
            angle = i * math.pi / 6
            factor = 1 - (i / 24)  # Gets smaller as we go
            x = center_x + int(math.cos(angle) * radius * factor)
            y = center_y + int(math.sin(angle) * radius * factor)
            points.append((x, y))
        
        if len(points) > 1:
            pygame.draw.lines(surface, color, False, points, 2)
    
    elif decoration_type == 'lines':
        for i in range(3):
            y = rect.y + rect.height * (i + 1) // 4
            pygame.draw.line(
                surface,
                color,
                (rect.x + 5, y),
                (rect.x + rect.width - 5, y),
                1
            )
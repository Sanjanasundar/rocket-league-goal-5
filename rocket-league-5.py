#!/usr/bin/env python3
"""
🚀 COSMIC ROCKET LEAGUE v2 — 5 Unique Levels Edition
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
LEVEL 1 — LUNAR COLOSSEUM    : Classic craters, dusty white terrain, low-grav rings
LEVEL 2 — NEBULA RIFT        : Glowing gas clouds, floating crystal shards, teal/magenta
LEVEL 3 — ASTEROID GRAVEYARD : Dense rock fields, spinning debris, orange/brown ruins
LEVEL 4 — BLACK HOLE STATION : Crimson void, spiraling gravity wells, dark corridors
LEVEL 5 — PULSAR CORE        : Electric cyan grid, lightning hazards, neon geometry
"""

import pygame
import math
import random
import numpy as np
import sys
import time
from dataclasses import dataclass, field
from typing import List, Tuple, Optional
from enum import Enum

# ─── CONFIG ───────────────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1280, 720
FPS = 60
BALL_RADIUS = 16
CAR_W, CAR_H = 36, 22
GOAL_W, GOAL_H = 22, 150
BOOST_MAX = 100.0
BOOST_RECHARGE = 8.0
BOOST_COST = 30.0
BOOST_SPEED = 520.0
MAX_SPEED = 380.0

# ─── LEVEL DEFINITIONS ───────────────────────────────────────────────────────
LEVELS = [
    {
        "id": 0,
        "name": "LUNAR COLOSSEUM",
        "subtitle": "The ancient arena of the moon",
        "gravity_strength": 0,
        "bg": (6, 8, 18),
        "accent": (180, 200, 255),
        "accent2": (100, 120, 200),
        "star_color": (220, 225, 255),
        "anomaly_types": ["repulsor"],
        "max_anomalies": 1,
        "max_asteroids": 0,
        "hazards": [],
        "description": "Zero gravity · Crater rings · Classic arena",
    },
    {
        "id": 1,
        "name": "NEBULA RIFT",
        "subtitle": "Lost in the gas clouds of Orion",
        "gravity_strength": 0,
        "bg": (4, 0, 18),
        "accent": (0, 255, 200),
        "accent2": (200, 0, 255),
        "star_color": (180, 100, 255),
        "anomaly_types": ["nebula", "repulsor"],
        "max_anomalies": 3,
        "max_asteroids": 0,
        "hazards": ["crystal_shards"],
        "description": "Nebula drag zones · Crystal obstacles · Dual tone",
    },
    {
        "id": 2,
        "name": "ASTEROID GRAVEYARD",
        "subtitle": "Ruins of a shattered world",
        "gravity_strength": 0,
        "bg": (12, 6, 0),
        "accent": (255, 140, 40),
        "accent2": (160, 80, 20),
        "star_color": (255, 200, 120),
        "anomaly_types": ["repulsor"],
        "max_anomalies": 2,
        "max_asteroids": 5,
        "hazards": ["spinning_rocks"],
        "description": "Dense asteroid field · Spinning debris · High chaos",
    },
    {
        "id": 3,
        "name": "BLACK HOLE STATION",
        "subtitle": "Event horizon — point of no return",
        "gravity_strength": 0,
        "bg": (8, 0, 2),
        "accent": (255, 40, 80),
        "accent2": (180, 0, 80),
        "star_color": (255, 100, 120),
        "anomaly_types": ["black_hole"],
        "max_anomalies": 2,
        "max_asteroids": 2,
        "hazards": ["gravity_corridors"],
        "description": "Black holes · Gravity corridors · Maximum danger",
    },
    {
        "id": 4,
        "name": "PULSAR CORE",
        "subtitle": "The beating heart of a neutron star",
        "gravity_strength": 0,
        "bg": (0, 8, 18),
        "accent": (0, 240, 255),
        "accent2": (255, 240, 0),
        "star_color": (100, 220, 255),
        "anomaly_types": ["repulsor", "nebula"],
        "max_anomalies": 2,
        "max_asteroids": 1,
        "hazards": ["pulse_rings", "lightning_nodes"],
        "description": "Pulse rings · Lightning nodes · Neon grid",
    },
]

# ─── MATH HELPERS ─────────────────────────────────────────────────────────────
def v2_len(v):     return math.sqrt(v[0]**2 + v[1]**2)
def v2_norm(v):
    l = v2_len(v)
    return (v[0]/l, v[1]/l) if l > 0.001 else (0, 0)
def lerp(a, b, t): return a + (b - a) * t
def clamp(v, lo, hi): return max(lo, min(hi, v))


# ─── PARTICLE SYSTEM ──────────────────────────────────────────────────────────
@dataclass
class Particle:
    x: float; y: float
    vx: float; vy: float
    life: float; max_life: float
    color: tuple; size: float
    fade: bool = True

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def emit(self, x, y, vx, vy, color, count=1, spread=2.0, life=0.8, size=3.0, fade=True):
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            spd = random.uniform(0, spread)
            self.particles.append(Particle(
                x, y,
                vx + math.cos(angle) * spd,
                vy + math.sin(angle) * spd,
                life, life, color, size, fade
            ))

    def update(self, dt):
        alive = []
        for p in self.particles:
            p.x += p.vx * dt
            p.y += p.vy * dt
            p.vx *= 0.97
            p.vy *= 0.97
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self.particles = alive

    def draw(self, surf):
        for p in self.particles:
            alpha = p.life / p.max_life if p.fade else 1.0
            r = int(p.color[0] * alpha)
            g = int(p.color[1] * alpha)
            b = int(p.color[2] * alpha)
            sz = max(1, int(p.size * alpha))
            pygame.draw.circle(surf, (r, g, b), (int(p.x), int(p.y)), sz)


# ─── HAZARDS ──────────────────────────────────────────────────────────────────
@dataclass
class CrystalShard:
    x: float; y: float; angle: float; size: float; spin: float

@dataclass
class GravityCorridor:
    x: float; y: float; width: float; height: float; strength: float; direction: float

@dataclass
class PulseRing:
    cx: float; cy: float; radius: float; max_radius: float; speed: float; color: tuple

@dataclass
class LightningNode:
    x: float; y: float; timer: float; active: bool; radius: float


# ─── TERRAIN LAYER ─────────────────────────────────────────────────────────────
class TerrainRenderer:
    """Draws the unique background terrain for each level."""

    def __init__(self, level_id: int, rng: random.Random):
        self.level_id = level_id
        self.rng = rng
        self._bake(level_id, rng)

    def _bake(self, lid, rng):
        """Pre-generate all terrain geometry."""
        self.elements = []  # (kind, data)

        if lid == 0:  # LUNAR COLOSSEUM
            self._bake_lunar(rng)
        elif lid == 1:  # NEBULA RIFT
            self._bake_nebula(rng)
        elif lid == 2:  # ASTEROID GRAVEYARD
            self._bake_asteroid_graveyard(rng)
        elif lid == 3:  # BLACK HOLE STATION
            self._bake_black_hole_station(rng)
        elif lid == 4:  # PULSAR CORE
            self._bake_pulsar_core(rng)

    def _bake_lunar(self, rng):
        # Stars — cold white/blue
        self.stars = [(rng.randint(0, SCREEN_W), rng.randint(0, SCREEN_H),
                       rng.randint(150, 255), rng.choice([1, 1, 2]))
                      for _ in range(200)]
        # Crater rings — concentric circles at random positions
        self.craters = []
        for _ in range(12):
            cx = rng.randint(80, SCREEN_W - 80)
            cy = rng.randint(80, SCREEN_H - 80)
            cr = rng.randint(20, 80)
            self.craters.append((cx, cy, cr))
        # Dusty ground patches — horizontal ellipses near bottom
        self.dust_patches = []
        for _ in range(8):
            px = rng.randint(50, SCREEN_W - 50)
            py = rng.randint(SCREEN_H - 150, SCREEN_H - 30)
            self.dust_patches.append((px, py, rng.randint(60, 180), rng.randint(10, 30)))
        # Rocky ridges — jagged polygon lines
        self.ridges = []
        for _ in range(3):
            y_base = rng.randint(SCREEN_H - 120, SCREEN_H - 40)
            pts = []
            x = 0
            while x < SCREEN_W:
                pts.append((x, y_base + rng.randint(-25, 25)))
                x += rng.randint(30, 80)
            pts.append((SCREEN_W, SCREEN_H))
            pts.append((0, SCREEN_H))
            self.ridges.append(pts)
        # Arena rings (decorative) — big circles
        self.arena_rings = [
            (SCREEN_W // 2, SCREEN_H // 2, 260),
            (SCREEN_W // 2, SCREEN_H // 2, 320),
        ]

    def _bake_nebula(self, rng):
        # Stars — magenta/teal hues
        self.stars = [(rng.randint(0, SCREEN_W), rng.randint(0, SCREEN_H),
                       rng.randint(100, 220), rng.choice([1, 1, 2, 3]))
                      for _ in range(250)]
        # Gas cloud blobs — large translucent ellipses
        self.gas_clouds = []
        for _ in range(15):
            self.gas_clouds.append({
                'x': rng.randint(0, SCREEN_W), 'y': rng.randint(0, SCREEN_H),
                'rx': rng.randint(60, 220), 'ry': rng.randint(40, 150),
                'hue': rng.choice(['teal', 'magenta', 'purple']),
                'alpha': rng.randint(15, 45)
            })
        # Crystal shard positions (decorative background)
        self.bg_crystals = []
        for _ in range(30):
            self.bg_crystals.append({
                'x': rng.randint(0, SCREEN_W), 'y': rng.randint(0, SCREEN_H),
                'size': rng.randint(4, 18), 'angle': rng.uniform(0, math.pi),
                'col': rng.choice([(0, 220, 180, 60), (200, 0, 255, 50), (0, 180, 255, 55)])
            })
        # Flowing nebula streaks
        self.streaks = []
        for _ in range(20):
            self.streaks.append({
                'x1': rng.randint(0, SCREEN_W), 'y1': rng.randint(0, SCREEN_H),
                'x2': rng.randint(0, SCREEN_W), 'y2': rng.randint(0, SCREEN_H),
                'col': rng.choice([(0,255,200,20),(180,0,255,18),(0,150,255,15)])
            })

    def _bake_asteroid_graveyard(self, rng):
        # Stars — warm orange
        self.stars = [(rng.randint(0, SCREEN_W), rng.randint(0, SCREEN_H),
                       rng.randint(100, 200), rng.choice([1, 1, 2]))
                      for _ in range(180)]
        # Background asteroid silhouettes (huge, dark, non-interactive)
        self.bg_asteroids = []
        for _ in range(25):
            cx = rng.randint(0, SCREEN_W)
            cy = rng.randint(0, SCREEN_H)
            r  = rng.randint(15, 70)
            pts = []
            for i in range(8):
                a = i * math.pi / 4 + rng.uniform(-0.3, 0.3)
                rd = r * rng.uniform(0.6, 1.0)
                pts.append((int(cx + math.cos(a) * rd), int(cy + math.sin(a) * rd)))
            alpha = rng.randint(30, 80)
            self.bg_asteroids.append({'pts': pts, 'alpha': alpha})
        # Rubble field — small rocks scattered around edges
        self.rubble = []
        for _ in range(60):
            self.rubble.append({
                'x': rng.randint(20, SCREEN_W - 20),
                'y': rng.randint(20, SCREEN_H - 20),
                'r': rng.randint(3, 10),
                'alpha': rng.randint(40, 120)
            })
        # Ruin arch fragments — partial ring arcs
        self.arches = []
        for _ in range(5):
            self.arches.append({
                'cx': rng.randint(100, SCREEN_W - 100),
                'cy': rng.randint(100, SCREEN_H - 100),
                'r':  rng.randint(50, 140),
                'start': rng.uniform(0, math.pi),
                'span':  rng.uniform(0.5, 2.5),
            })
        # Dust column streaks (vertical)
        self.dust_cols = []
        for _ in range(12):
            self.dust_cols.append({
                'x': rng.randint(0, SCREEN_W),
                'y': rng.randint(0, SCREEN_H),
                'h': rng.randint(40, 200),
                'w': rng.randint(3, 10),
                'alpha': rng.randint(10, 35)
            })

    def _bake_black_hole_station(self, rng):
        # Stars — deep red
        self.stars = [(rng.randint(0, SCREEN_W), rng.randint(0, SCREEN_H),
                       rng.randint(80, 180), rng.choice([1, 1, 2]))
                      for _ in range(160)]
        # Station corridor panels — dark rectangles on edges
        self.panels = []
        for _ in range(18):
            side = rng.choice(['top', 'bottom', 'left', 'right'])
            if side == 'top':
                self.panels.append(pygame.Rect(rng.randint(0, SCREEN_W - 80), rng.randint(64, 130),
                                               rng.randint(40, 120), rng.randint(8, 25)))
            elif side == 'bottom':
                self.panels.append(pygame.Rect(rng.randint(0, SCREEN_W - 80), rng.randint(SCREEN_H - 130, SCREEN_H - 64),
                                               rng.randint(40, 120), rng.randint(8, 25)))
            elif side == 'left':
                self.panels.append(pygame.Rect(rng.randint(10, 100), rng.randint(64, SCREEN_H - 64),
                                               rng.randint(8, 22), rng.randint(30, 100)))
            else:
                self.panels.append(pygame.Rect(rng.randint(SCREEN_W - 110, SCREEN_W - 30), rng.randint(64, SCREEN_H - 64),
                                               rng.randint(8, 22), rng.randint(30, 100)))
        # Warning stripes — diagonal danger zones
        self.warning_stripes = []
        for _ in range(6):
            self.warning_stripes.append({
                'x': rng.randint(50, SCREEN_W - 50),
                'y': rng.randint(80, SCREEN_H - 80),
                'w': rng.randint(30, 80),
                'h': rng.randint(100, 220),
                'angle': rng.uniform(-0.4, 0.4)
            })
        # Glowing red event horizons (decorative small circles)
        self.mini_horizons = []
        for _ in range(8):
            self.mini_horizons.append({
                'x': rng.randint(60, SCREEN_W - 60),
                'y': rng.randint(80, SCREEN_H - 80),
                'r': rng.randint(8, 22),
            })

    def _bake_pulsar_core(self, rng):
        # Stars — bright electric
        self.stars = [(rng.randint(0, SCREEN_W), rng.randint(0, SCREEN_H),
                       rng.randint(150, 255), rng.choice([1, 1, 2, 2, 3]))
                      for _ in range(300)]
        # Neon grid lines — horizontal and vertical
        self.grid_h = list(range(64, SCREEN_H, rng.randint(55, 80)))
        self.grid_v = list(range(0, SCREEN_W, rng.randint(55, 80)))
        # Hexagonal node positions
        self.hex_nodes = []
        for r in range(4):
            for c in range(7):
                hx = 100 + c * 175 + (80 if r % 2 else 0)
                hy = 140 + r * 155
                if 60 < hx < SCREEN_W - 60 and 80 < hy < SCREEN_H - 80:
                    self.hex_nodes.append((hx, hy, rng.randint(18, 35)))
        # Diagonal energy beams
        self.energy_beams = []
        for _ in range(10):
            self.energy_beams.append({
                'x1': rng.randint(0, SCREEN_W), 'y1': rng.randint(64, SCREEN_H),
                'x2': rng.randint(0, SCREEN_W), 'y2': rng.randint(64, SCREEN_H),
                'alpha': rng.randint(8, 25)
            })

    def draw(self, surf, t: float):
        lid = self.level_id
        if lid == 0:   self._draw_lunar(surf, t)
        elif lid == 1: self._draw_nebula(surf, t)
        elif lid == 2: self._draw_asteroid_graveyard(surf, t)
        elif lid == 3: self._draw_black_hole_station(surf, t)
        elif lid == 4: self._draw_pulsar_core(surf, t)

    # ── LEVEL 0: LUNAR ────────────────────────────────────────────────────────
    def _draw_lunar(self, surf, t):
        # Stars
        for sx, sy, sb, ss in self.stars:
            pygame.draw.circle(surf, (sb, sb, min(255, sb + 30)), (sx, sy), ss)

        # Dust patches
        ds = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for px, py, pw, ph in self.dust_patches:
            pygame.draw.ellipse(ds, (180, 190, 220, 22), (px - pw, py - ph, pw * 2, ph * 2))
        surf.blit(ds, (0, 0))

        # Rocky ridges
        for pts in self.ridges:
            pygame.draw.polygon(surf, (28, 32, 52), pts)
            pygame.draw.lines(surf, (60, 70, 110), False, pts[:-2], 2)

        # Crater circles
        cs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for cx, cy, cr in self.craters:
            pygame.draw.circle(cs, (100, 120, 180, 20), (cx, cy), cr)
            pygame.draw.circle(cs, (140, 160, 220, 35), (cx, cy), cr, 2)
            pygame.draw.circle(cs, (160, 180, 255, 15), (cx, cy), int(cr * 0.5))
        surf.blit(cs, (0, 0))

        # Arena rings (animated slow pulse)
        pulse = 0.5 + 0.5 * math.sin(t * 0.8)
        for cx, cy, cr in self.arena_rings:
            a = pygame.Surface((cr * 2 + 4, cr * 2 + 4), pygame.SRCALPHA)
            alpha = int(30 + pulse * 20)
            pygame.draw.circle(a, (140, 160, 255, alpha), (cr + 2, cr + 2), cr, 2)
            surf.blit(a, (cx - cr - 2, cy - cr - 2))

    # ── LEVEL 1: NEBULA ───────────────────────────────────────────────────────
    def _draw_nebula(self, surf, t):
        # Stars with tinted colors
        for sx, sy, sb, ss in self.stars:
            tint = [(sb, int(sb * 0.3), sb), (int(sb * 0.3), sb, int(sb * 0.8))]
            col = tint[(sx + sy) % 2]
            pygame.draw.circle(surf, col, (sx, sy), ss)

        # Gas clouds
        gs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for cloud in self.gas_clouds:
            drift = math.sin(t * 0.3 + cloud['x'] * 0.01) * 8
            if cloud['hue'] == 'teal':    col = (0, 230, 200, cloud['alpha'])
            elif cloud['hue'] == 'magenta': col = (220, 0, 255, cloud['alpha'])
            else:                           col = (120, 0, 200, cloud['alpha'])
            pygame.draw.ellipse(gs, col,
                (cloud['x'] - cloud['rx'] + drift, cloud['y'] - cloud['ry'],
                 cloud['rx'] * 2, cloud['ry'] * 2))
        surf.blit(gs, (0, 0))

        # Streaks
        ss2 = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for sk in self.streaks:
            pygame.draw.line(ss2, sk['col'], (sk['x1'], sk['y1']), (sk['x2'], sk['y2']), 1)
        surf.blit(ss2, (0, 0))

        # Background crystals
        cs = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for cr in self.bg_crystals:
            a = cr['angle'] + t * 0.2
            hw = cr['size']; hh = cr['size'] * 3
            pts = [
                (cr['x'] + math.cos(a) * hw,          cr['y'] + math.sin(a) * hw),
                (cr['x'] + math.cos(a + 1.5) * hh * 0.3, cr['y'] + math.sin(a + 1.5) * hh * 0.3),
                (cr['x'] + math.cos(a + math.pi) * hw, cr['y'] + math.sin(a + math.pi) * hw),
                (cr['x'] + math.cos(a - 1.5) * hh * 0.3, cr['y'] + math.sin(a - 1.5) * hh * 0.3),
            ]
            pts_int = [(int(p[0]), int(p[1])) for p in pts]
            if len(pts_int) >= 3:
                pygame.draw.polygon(cs, cr['col'], pts_int)
        surf.blit(cs, (0, 0))

    # ── LEVEL 2: ASTEROID GRAVEYARD ───────────────────────────────────────────
    def _draw_asteroid_graveyard(self, surf, t):
        # Stars with warm tint
        for sx, sy, sb, ss in self.stars:
            pygame.draw.circle(surf, (sb, int(sb * 0.7), int(sb * 0.3)), (sx, sy), ss)

        # Dust columns
        dc = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for col in self.dust_cols:
            drift = math.sin(t * 0.4 + col['x'] * 0.02) * 5
            pygame.draw.rect(dc, (200, 120, 60, col['alpha']),
                (col['x'] + drift, col['y'], col['w'], col['h']))
        surf.blit(dc, (0, 0))

        # Ruin arches
        arch_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for arch in self.arches:
            rect = pygame.Rect(arch['cx'] - arch['r'], arch['cy'] - arch['r'],
                               arch['r'] * 2, arch['r'] * 2)
            pygame.draw.arc(arch_s, (180, 100, 40, 70), rect,
                            arch['start'], arch['start'] + arch['span'], 4)
        surf.blit(arch_s, (0, 0))

        # Background asteroids
        ba = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for ast in self.bg_asteroids:
            pygame.draw.polygon(ba, (100, 60, 20, ast['alpha']), ast['pts'])
            pygame.draw.polygon(ba, (160, 100, 50, ast['alpha'] + 20), ast['pts'], 2)
        surf.blit(ba, (0, 0))

        # Rubble
        rb = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for rub in self.rubble:
            pygame.draw.circle(rb, (150, 90, 40, rub['alpha']), (rub['x'], rub['y']), rub['r'])
        surf.blit(rb, (0, 0))

    # ── LEVEL 3: BLACK HOLE STATION ───────────────────────────────────────────
    def _draw_black_hole_station(self, surf, t):
        # Stars (dim red)
        for sx, sy, sb, ss in self.stars:
            pygame.draw.circle(surf, (sb, int(sb * 0.2), int(sb * 0.2)), (sx, sy), ss)

        # Station panels
        ps = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for panel in self.panels:
            pygame.draw.rect(ps, (60, 0, 10, 150), panel)
            pygame.draw.rect(ps, (200, 30, 60, 180), panel, 1)
        surf.blit(ps, (0, 0))

        # Warning stripes (static danger zones)
        ws = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for stripe in self.warning_stripes:
            pulse = 0.3 + 0.3 * math.sin(t * 2 + stripe['x'] * 0.1)
            alpha = int(10 + pulse * 15)
            rect_surf = pygame.Surface((stripe['w'], stripe['h']), pygame.SRCALPHA)
            # Draw diagonal lines
            for i in range(0, stripe['w'] + stripe['h'], 14):
                pygame.draw.line(rect_surf, (255, 30, 60, alpha),
                                 (i, 0), (max(0, i - stripe['h']), stripe['h']), 3)
            ws.blit(rect_surf, (stripe['x'] - stripe['w'] // 2, stripe['y'] - stripe['h'] // 2))
        surf.blit(ws, (0, 0))

        # Mini event horizons (pulsing)
        mh = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for mh_data in self.mini_horizons:
            pulse = 0.5 + 0.5 * math.sin(t * 3 + mh_data['x'])
            r = mh_data['r']
            pygame.draw.circle(mh, (200, 0, 40, int(40 + pulse * 30)), (mh_data['x'], mh_data['y']), r)
            pygame.draw.circle(mh, (255, 60, 100, int(80 + pulse * 40)), (mh_data['x'], mh_data['y']), r, 2)
        surf.blit(mh, (0, 0))

    # ── LEVEL 4: PULSAR CORE ──────────────────────────────────────────────────
    def _draw_pulsar_core(self, surf, t):
        # Stars (bright, varied)
        for sx, sy, sb, ss in self.stars:
            twinkle = int(sb * (0.7 + 0.3 * math.sin(t * 3 + sx * 0.1)))
            pygame.draw.circle(surf, (int(twinkle * 0.4), twinkle, twinkle), (sx, sy), ss)

        # Grid
        grid_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pulse = int(8 + 6 * math.sin(t * 1.5))
        for gy in self.grid_h:
            pygame.draw.line(grid_s, (0, 200, 255, pulse), (0, gy), (SCREEN_W, gy), 1)
        for gx in self.grid_v:
            pygame.draw.line(grid_s, (0, 200, 255, pulse), (gx, 64), (gx, SCREEN_H), 1)
        surf.blit(grid_s, (0, 0))

        # Hex nodes
        hn = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for hx, hy, hr in self.hex_nodes:
            pulse2 = 0.5 + 0.5 * math.sin(t * 2 + hx * 0.05)
            alpha = int(20 + pulse2 * 35)
            pts = [(int(hx + math.cos(math.radians(a)) * hr),
                    int(hy + math.sin(math.radians(a)) * hr))
                   for a in range(0, 360, 60)]
            pygame.draw.polygon(hn, (0, 220, 255, alpha), pts)
            pygame.draw.polygon(hn, (0, 255, 255, alpha + 40), pts, 1)
        surf.blit(hn, (0, 0))

        # Energy beams
        eb = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        for beam in self.energy_beams:
            flicker = int(beam['alpha'] * (0.5 + 0.5 * math.sin(t * 4 + beam['x1'])))
            pygame.draw.line(eb, (255, 240, 0, flicker),
                             (beam['x1'], beam['y1']), (beam['x2'], beam['y2']), 1)
        surf.blit(eb, (0, 0))


# ─── GRAVITY ANOMALY ──────────────────────────────────────────────────────────
@dataclass
class GravityAnomaly:
    x: float; y: float
    radius: float; strength: float
    kind: str  # "black_hole" | "repulsor" | "nebula"

@dataclass
class BoostPad:
    x: float; y: float
    radius: float = 22
    active: bool = True
    cooldown: float = 0.0

@dataclass
class MovingAsteroid:
    x: float; y: float
    radius: float
    vx: float; vy: float
    angle: float = 0.0
    spin: float = 0.0
    # Level 2 asteroids can spin fast; level 3 slow drift
    color: tuple = (130, 110, 90)


# ─── LEVEL MAP ────────────────────────────────────────────────────────────────
class LevelMap:
    def __init__(self, level_id: int):
        self.level_id = level_id
        self.cfg = LEVELS[level_id]
        rng = random.Random(level_id * 137 + 42)
        self.rng = rng

        self.anomalies:   List[GravityAnomaly] = []
        self.boost_pads:  List[BoostPad]       = []
        self.asteroids:   List[MovingAsteroid] = []
        self.pulse_rings: List[PulseRing]      = []
        self.lightning:   List[LightningNode]  = []
        self.crystal_shards: List[CrystalShard] = []
        self.gravity_corridors: List[GravityCorridor] = []

        self.terrain = TerrainRenderer(level_id, rng)
        self._generate()

    def _generate(self):
        rng = self.rng
        cfg = self.cfg

        # ── Boost pads ──
        pads = [(SCREEN_W // 2, SCREEN_H // 2)]
        for _ in range(rng.randint(3, 6)):
            pads.append((rng.randint(120, SCREEN_W - 120), rng.randint(90, SCREEN_H - 90)))
        for px, py in pads:
            self.boost_pads.append(BoostPad(px, py))

        # ── Gravity anomalies ──
        kinds = cfg["anomaly_types"]
        for _ in range(cfg["max_anomalies"]):
            kind = rng.choice(kinds)
            ax = rng.randint(220, SCREEN_W - 220)
            ay = rng.randint(130, SCREEN_H - 130)
            r  = rng.randint(55, 115)
            s  = rng.uniform(100, 220) if kind == "black_hole" else rng.uniform(-50, -110)
            if kind == "nebula": s = rng.uniform(25, 55)
            self.anomalies.append(GravityAnomaly(ax, ay, r, s, kind))

        # ── Moving asteroids ──
        for _ in range(cfg["max_asteroids"]):
            lid = self.level_id
            spd = 60 if lid == 3 else 80  # slower in BH station
            col = {
                2: (160, 100, 50),
                3: (120, 20, 40),
            }.get(lid, (130, 110, 90))
            self.asteroids.append(MovingAsteroid(
                rng.randint(200, SCREEN_W - 200), rng.randint(90, SCREEN_H - 90),
                rng.randint(14, 32),
                rng.uniform(-spd, spd), rng.uniform(-spd * 0.8, spd * 0.8),
                rng.uniform(0, math.pi * 2),
                rng.uniform(-2.5, 2.5),
                col
            ))

        # ── Level-specific hazards ──
        hazards = cfg["hazards"]

        if "crystal_shards" in hazards:
            for _ in range(8):
                self.crystal_shards.append(CrystalShard(
                    rng.randint(100, SCREEN_W - 100), rng.randint(80, SCREEN_H - 80),
                    rng.uniform(0, math.pi * 2),
                    rng.randint(18, 45),
                    rng.uniform(-0.8, 0.8)
                ))

        if "gravity_corridors" in hazards:
            for _ in range(3):
                self.gravity_corridors.append(GravityCorridor(
                    rng.randint(200, SCREEN_W - 200), rng.randint(100, SCREEN_H - 100),
                    rng.randint(40, 80), rng.randint(80, 180),
                    rng.uniform(150, 300),
                    rng.uniform(0, math.pi * 2)
                ))

        if "pulse_rings" in hazards:
            for _ in range(3):
                self.pulse_rings.append(PulseRing(
                    rng.randint(200, SCREEN_W - 200), rng.randint(100, SCREEN_H - 100),
                    10, rng.randint(80, 160),
                    rng.uniform(80, 160),
                    self.cfg["accent"]
                ))

        if "lightning_nodes" in hazards:
            for _ in range(5):
                self.lightning.append(LightningNode(
                    rng.randint(150, SCREEN_W - 150), rng.randint(80, SCREEN_H - 80),
                    rng.uniform(1.5, 4.0), False,
                    rng.randint(50, 90)
                ))

    def update(self, dt: float):
        # Boost pad cooldowns
        for pad in self.boost_pads:
            if not pad.active:
                pad.cooldown -= dt
                if pad.cooldown <= 0:
                    pad.active = True

        # Asteroids
        for ast in self.asteroids:
            ast.x += ast.vx * dt
            ast.y += ast.vy * dt
            ast.angle += ast.spin * dt
            if ast.x < ast.radius or ast.x > SCREEN_W - ast.radius: ast.vx *= -1
            if ast.y < ast.radius or ast.y > SCREEN_H - ast.radius: ast.vy *= -1

        # Crystal shards (orbit slowly)
        for cs in self.crystal_shards:
            cs.angle += cs.spin * dt

        # Pulse rings
        for pr in self.pulse_rings:
            pr.radius += pr.speed * dt
            if pr.radius > pr.max_radius:
                pr.radius = 10

        # Lightning nodes
        for ln in self.lightning:
            ln.timer -= dt
            if ln.timer <= 0:
                ln.active = not ln.active
                ln.timer = random.uniform(0.4, 2.5) if ln.active else random.uniform(1.0, 4.0)

    def apply_gravity(self, ox, oy, vx, vy, mass=1.0, dt=0.016):
        for a in self.anomalies:
            dx = a.x - ox; dy = a.y - oy
            dist = max(1, math.sqrt(dx**2 + dy**2))
            if a.kind == "nebula":
                if dist < a.radius:
                    vx *= (1 - 0.35 * dt)
                    vy *= (1 - 0.35 * dt)
            else:
                if dist < a.radius * 3:
                    force = (a.strength / (dist**1.2)) * dt / mass
                    nx, ny = dx / dist, dy / dist
                    vx += nx * force; vy += ny * force

        # Gravity corridors (level 3)
        for gc in self.gravity_corridors:
            dx = ox - gc.x; dy = oy - gc.y
            # Corridor check (simple rectangle)
            if abs(dx) < gc.width / 2 and abs(dy) < gc.height / 2:
                nx = math.cos(gc.direction)
                ny = math.sin(gc.direction)
                vx += nx * gc.strength * dt / mass
                vy += ny * gc.strength * dt / mass

        return vx, vy

    def check_hazard_hit(self, ox, oy, radius) -> bool:
        """Returns True if object touches a hazard."""
        # Lightning nodes
        for ln in self.lightning:
            if ln.active:
                d = math.sqrt((ox - ln.x)**2 + (oy - ln.y)**2)
                if d < ln.radius + radius:
                    return True
        # Pulse rings (thin ring collision)
        for pr in self.pulse_rings:
            d = math.sqrt((ox - pr.cx)**2 + (oy - pr.cy)**2)
            if abs(d - pr.radius) < 10 + radius:
                return True
        return False

    def draw(self, surf, t: float):
        self.terrain.draw(surf, t)

        # Anomalies
        for a in self.anomalies:
            if   a.kind == "black_hole": self._draw_bh(surf, a, t)
            elif a.kind == "repulsor":   self._draw_repulsor(surf, a, t)
            elif a.kind == "nebula":     self._draw_nebula_zone(surf, a, t)

        # Asteroids
        for ast in self.asteroids:
            self._draw_asteroid(surf, ast)

        # Crystal shards
        for cs in self.crystal_shards:
            self._draw_crystal(surf, cs, t)

        # Pulse rings
        for pr in self.pulse_rings:
            self._draw_pulse_ring(surf, pr, t)

        # Lightning nodes
        for ln in self.lightning:
            self._draw_lightning(surf, ln, t)

        # Gravity corridors
        for gc in self.gravity_corridors:
            self._draw_corridor(surf, gc, t)

        # Boost pads
        self._draw_boosts(surf, t)

    def _draw_bh(self, surf, a, t):
        for i in range(5, 0, -1):
            r = int(a.radius * i / 5)
            alpha = 70 - i * 12
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (140, 0, 60, max(0, alpha)), (r, r), r)
            surf.blit(s, (int(a.x) - r, int(a.y) - r))
        pygame.draw.circle(surf, (8, 0, 2), (int(a.x), int(a.y)), int(a.radius * 0.28))
        for i in range(10):
            ang = t * 2.5 + i * math.pi / 5
            r1, r2 = a.radius * 0.32, a.radius * 0.95
            x1 = a.x + math.cos(ang) * r1
            y1 = a.y + math.sin(ang) * r1
            x2 = a.x + math.cos(ang + 0.7) * r2
            y2 = a.y + math.sin(ang + 0.7) * r2
            pygame.draw.line(surf, (255, 40, 100, 150), (int(x1), int(y1)), (int(x2), int(y2)), 1)

    def _draw_repulsor(self, surf, a, t):
        pulse = 0.5 + 0.5 * math.sin(t * 2)
        s = pygame.Surface((int(a.radius * 2), int(a.radius * 2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 180, 255, int(18 + pulse * 15)),
                           (int(a.radius), int(a.radius)), int(a.radius))
        surf.blit(s, (int(a.x - a.radius), int(a.y - a.radius)))
        pygame.draw.circle(surf, (0, 200, 255), (int(a.x), int(a.y)), int(a.radius), 1)
        pygame.draw.circle(surf, (120, 220, 255), (int(a.x), int(a.y)), 7)

    def _draw_nebula_zone(self, surf, a, t):
        for i in range(3):
            r = int(a.radius * (1 - i * 0.25))
            alpha = 12 + i * 8
            s = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            col = (60, 0, 140) if i % 2 == 0 else (0, 200, 160)
            pygame.draw.circle(s, (*col, alpha), (r, r), r)
            surf.blit(s, (int(a.x) - r, int(a.y) - r))
        pygame.draw.circle(surf, (80, 0, 180), (int(a.x), int(a.y)), int(a.radius), 1)

    def _draw_asteroid(self, surf, ast):
        pts = []
        for i in range(10):
            ang = ast.angle + i * math.pi / 5
            r = ast.radius * (0.65 + 0.35 * ((i * 7 + 3) % 5) / 4)
            pts.append((int(ast.x + math.cos(ang) * r), int(ast.y + math.sin(ang) * r)))
        if len(pts) >= 3:
            pygame.draw.polygon(surf, ast.color, pts)
            lighter = tuple(min(255, c + 50) for c in ast.color)
            pygame.draw.polygon(surf, lighter, pts, 2)

    def _draw_crystal(self, surf, cs, t):
        a = cs.angle
        hw = cs.size * 0.4; hh = cs.size
        pts = [
            (cs.x + math.cos(a) * hw,          cs.y + math.sin(a) * hw),
            (cs.x + math.cos(a + 1.57) * hh,   cs.y + math.sin(a + 1.57) * hh),
            (cs.x + math.cos(a + math.pi) * hw, cs.y + math.sin(a + math.pi) * hw),
            (cs.x + math.cos(a - 1.57) * hh,   cs.y + math.sin(a - 1.57) * hh),
        ]
        pts_i = [(int(p[0]), int(p[1])) for p in pts]
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        if len(pts_i) >= 3:
            pygame.draw.polygon(s, (0, 220, 200, 160), pts_i)
            pygame.draw.polygon(s, (0, 255, 220, 220), pts_i, 2)
        surf.blit(s, (0, 0))

    def _draw_pulse_ring(self, surf, pr, t):
        alpha = int(180 * (1 - pr.radius / pr.max_radius))
        if alpha > 5:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(s, (*pr.color, alpha), (int(pr.cx), int(pr.cy)), int(pr.radius), 3)
            surf.blit(s, (0, 0))

    def _draw_lightning(self, surf, ln, t):
        if ln.active:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flicker = 0.5 + 0.5 * math.sin(t * 20)
            alpha = int(100 + flicker * 155)
            pygame.draw.circle(s, (0, 240, 255, alpha), (int(ln.x), int(ln.y)), int(ln.radius))
            pygame.draw.circle(s, (255, 255, 255, alpha), (int(ln.x), int(ln.y)), int(ln.radius), 3)
            # Lightning bolts
            for bolt in range(5):
                ang = t * 5 + bolt * math.pi * 2 / 5
                ex = ln.x + math.cos(ang) * ln.radius
                ey = ln.y + math.sin(ang) * ln.radius
                ex2 = ex + random.uniform(-20, 20)
                ey2 = ey + random.uniform(-20, 20)
                pygame.draw.line(s, (0, 255, 255, alpha), (int(ln.x), int(ln.y)), (int(ex2), int(ey2)), 2)
            surf.blit(s, (0, 0))
        else:
            s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            pygame.draw.circle(s, (0, 80, 100, 60), (int(ln.x), int(ln.y)), int(ln.radius), 1)
            surf.blit(s, (0, 0))

    def _draw_corridor(self, surf, gc, t):
        pulse = 0.3 + 0.2 * math.sin(t * 1.5 + gc.x * 0.01)
        s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        # Draw corridor as oriented rect
        hw, hh = gc.width / 2, gc.height / 2
        cos_a, sin_a = math.cos(gc.direction), math.sin(gc.direction)
        corners = [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]
        pts = [(int(gc.x + cx * cos_a - cy * sin_a), int(gc.y + cx * sin_a + cy * cos_a))
               for cx, cy in corners]
        pygame.draw.polygon(s, (255, 30, 60, int(pulse * 30)), pts)
        pygame.draw.polygon(s, (255, 60, 90, 80), pts, 2)
        surf.blit(s, (0, 0))

    def _draw_boosts(self, surf, t):
        pulse = 0.5 + 0.5 * math.sin(t * 3)
        col = self.cfg["accent"]
        for pad in self.boost_pads:
            if pad.active:
                s = pygame.Surface((pad.radius * 5, pad.radius * 5), pygame.SRCALPHA)
                pygame.draw.circle(s, (*col, int(30 + pulse * 25)),
                                   (pad.radius * 2, pad.radius * 2), pad.radius * 2)
                surf.blit(s, (int(pad.x) - pad.radius * 2, int(pad.y) - pad.radius * 2))
                pygame.draw.circle(surf, col, (int(pad.x), int(pad.y)), pad.radius, 2)
                # Inner cross
                r = pad.radius // 2
                pygame.draw.line(surf, col, (int(pad.x) - r, int(pad.y)), (int(pad.x) + r, int(pad.y)), 2)
                pygame.draw.line(surf, col, (int(pad.x), int(pad.y) - r), (int(pad.x), int(pad.y) + r), 2)
            else:
                pygame.draw.circle(surf, (50, 55, 70), (int(pad.x), int(pad.y)), pad.radius, 1)


# ─── CAR ──────────────────────────────────────────────────────────────────────
class Car:
    def __init__(self, x, y, is_player=True, level_cfg=None):
        self.x = float(x); self.y = float(y)
        self.vx = 0.0; self.vy = 0.0
        self.angle = 0.0
        self.is_player = is_player
        self.boost = BOOST_MAX
        self.score = 0
        self.boosting = False
        self.trail: List[Tuple] = []
        self.invincible = 0.0
        cfg = level_cfg or LEVELS[0]
        self.color  = cfg["accent"]  if is_player else cfg["accent2"]
        self.color2 = tuple(max(0, c - 80) for c in self.color)

    @property
    def rect(self):
        return pygame.Rect(self.x - CAR_W//2, self.y - CAR_H//2, CAR_W, CAR_H)

    def apply_input(self, left, right, forward, back, boost_key, dt):
        rot_spd = 220 * dt
        if left:  self.angle -= rot_spd * (math.pi / 180)
        if right: self.angle += rot_spd * (math.pi / 180)
        accel = 400
        if forward:
            self.vx += math.cos(self.angle) * accel * dt
            self.vy += math.sin(self.angle) * accel * dt
        if back:
            self.vx -= math.cos(self.angle) * accel * 0.5 * dt
            self.vy -= math.sin(self.angle) * accel * 0.5 * dt
        self.boosting = boost_key and self.boost > 5 and forward
        if self.boosting:
            self.vx += math.cos(self.angle) * BOOST_SPEED * dt
            self.vy += math.sin(self.angle) * BOOST_SPEED * dt
            self.boost -= BOOST_COST * dt
        else:
            self.boost = min(BOOST_MAX, self.boost + BOOST_RECHARGE * dt)
        spd = v2_len((self.vx, self.vy))
        max_s = BOOST_SPEED if self.boosting else MAX_SPEED
        if spd > max_s:
            scale = max_s / spd
            self.vx *= scale; self.vy *= scale
        drag = 0.992 if not forward and not back else 0.999
        self.vx *= drag; self.vy *= drag

    def update(self, dt, level_map: LevelMap):
        self.vx, self.vy = level_map.apply_gravity(self.x, self.y, self.vx, self.vy, dt=dt)
        self.x += self.vx * dt; self.y += self.vy * dt
        self.trail.append((self.x, self.y))
        if len(self.trail) > 22: self.trail.pop(0)
        pad = 30
        if self.x < pad:          self.x = pad;            self.vx = abs(self.vx) * 0.6
        if self.x > SCREEN_W - pad: self.x = SCREEN_W - pad; self.vx = -abs(self.vx) * 0.6
        if self.y < pad:           self.y = pad;             self.vy = abs(self.vy) * 0.6
        if self.y > SCREEN_H - pad: self.y = SCREEN_H - pad; self.vy = -abs(self.vy) * 0.6
        for ast in level_map.asteroids:
            dx = self.x - ast.x; dy = self.y - ast.y
            d = math.sqrt(dx**2 + dy**2)
            min_d = ast.radius + max(CAR_W, CAR_H) // 2
            if d < min_d and d > 0.1:
                nx, ny = dx / d, dy / d
                self.vx += nx * 220; self.vy += ny * 220
        if self.invincible > 0: self.invincible -= dt
        for bp in level_map.boost_pads:
            if bp.active:
                dx = self.x - bp.x; dy = self.y - bp.y
                if math.sqrt(dx**2 + dy**2) < bp.radius + 16:
                    self.boost = min(BOOST_MAX, self.boost + 45)
                    bp.active = False; bp.cooldown = 5.0

    def draw(self, surf, particles: ParticleSystem):
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / max(1, len(self.trail))
            r = int(self.color[0] * alpha * 0.5)
            g = int(self.color[1] * alpha * 0.5)
            b = int(self.color[2] * alpha * 0.5)
            pygame.draw.circle(surf, (r, g, b), (int(tx), int(ty)), max(1, int(3 * alpha)))
        if self.boosting:
            bx = self.x - math.cos(self.angle) * 20
            by = self.y - math.sin(self.angle) * 20
            particles.emit(bx, by, -math.cos(self.angle)*80, -math.sin(self.angle)*80,
                           (255, 180, 0), count=3, spread=30, life=0.3, size=4)
        cos_a, sin_a = math.cos(self.angle), math.sin(self.angle)
        def rot(px, py):
            return (int(self.x + px*cos_a - py*sin_a), int(self.y + px*sin_a + py*cos_a))
        body = [rot(-CAR_W//2, -CAR_H//2), rot(CAR_W//2, -8), rot(CAR_W//2, 8), rot(-CAR_W//2, CAR_H//2)]
        pygame.draw.polygon(surf, self.color2, body)
        pygame.draw.polygon(surf, self.color, body, 2)
        cock = [rot(0, -CAR_H//4), rot(CAR_W//3, -4), rot(CAR_W//3, 4), rot(0, CAR_H//4)]
        pygame.draw.polygon(surf, (200, 240, 255), cock)
        eg_x, eg_y = rot(-CAR_W//2, 0)
        s = pygame.Surface((20, 20), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 180, 0, 160 if self.boosting else 60), (10, 10), 8)
        surf.blit(s, (eg_x - 10, eg_y - 10))


# ─── BALL ─────────────────────────────────────────────────────────────────────
class Ball:
    def __init__(self):
        self.reset()

    def reset(self):
        self.x = float(SCREEN_W // 2); self.y = float(SCREEN_H // 2)
        self.vx = random.uniform(-120, 120); self.vy = random.uniform(-90, 90)
        self.trail: List[Tuple] = []
        self.spin = 0.0

    def update(self, dt, level_map: LevelMap):
        self.vx, self.vy = level_map.apply_gravity(self.x, self.y, self.vx, self.vy, mass=0.7, dt=dt)
        self.x += self.vx * dt; self.y += self.vy * dt
        self.spin += 0.05
        self.trail.append((self.x, self.y))
        if len(self.trail) > 16: self.trail.pop(0)
        if self.x < BALL_RADIUS:             self.x = BALL_RADIUS;             self.vx = abs(self.vx)*0.9
        if self.x > SCREEN_W - BALL_RADIUS:  self.x = SCREEN_W - BALL_RADIUS;  self.vx = -abs(self.vx)*0.9
        if self.y < BALL_RADIUS:             self.y = BALL_RADIUS;             self.vy = abs(self.vy)*0.9
        if self.y > SCREEN_H - BALL_RADIUS:  self.y = SCREEN_H - BALL_RADIUS;  self.vy = -abs(self.vy)*0.9
        for ast in level_map.asteroids:
            dx = self.x - ast.x; dy = self.y - ast.y
            d = math.sqrt(dx**2 + dy**2)
            if d < BALL_RADIUS + ast.radius and d > 0.1:
                nx, ny = dx/d, dy/d
                spd = v2_len((self.vx, self.vy))
                self.vx = nx * max(spd, 160); self.vy = ny * max(spd, 160)
                self.x = ast.x + nx * (BALL_RADIUS + ast.radius + 2)
                self.y = ast.y + ny * (BALL_RADIUS + ast.radius + 2)
        spd = v2_len((self.vx, self.vy))
        if spd > 750: self.vx = self.vx/spd*750; self.vy = self.vy/spd*750

    def car_hit(self, car: Car, particles: ParticleSystem):
        dx = self.x - car.x; dy = self.y - car.y
        d = math.sqrt(dx**2 + dy**2)
        min_d = BALL_RADIUS + max(CAR_W, CAR_H) // 2
        if d < min_d and d > 0.1:
            nx, ny = dx/d, dy/d
            car_spd = v2_len((car.vx, car.vy))
            impact = max(car_spd * 0.8, 260) + (200 if car.boosting else 0)
            self.vx = nx*impact + car.vx*0.3; self.vy = ny*impact + car.vy*0.3
            car.vx -= nx*80; car.vy -= ny*80
            self.x = car.x + nx*(min_d+2); self.y = car.y + ny*(min_d+2)
            particles.emit(self.x, self.y, 0, 0, (255,180,0), count=12, spread=130, life=0.4, size=4)
            return True
        return False

    def draw(self, surf, level_cfg: dict):
        col = level_cfg["accent"]
        for i, (tx, ty) in enumerate(self.trail):
            alpha = i / max(1, len(self.trail))
            r = int(col[0]*alpha); g = int(col[1]*alpha*0.7); b = int(col[2]*alpha*0.5)
            pygame.draw.circle(surf, (r,g,b), (int(tx),int(ty)), max(1, int(BALL_RADIUS*0.4*alpha)))
        gs = pygame.Surface((BALL_RADIUS*6, BALL_RADIUS*6), pygame.SRCALPHA)
        pygame.draw.circle(gs, (*col, 45), (BALL_RADIUS*3, BALL_RADIUS*3), BALL_RADIUS*3)
        surf.blit(gs, (int(self.x)-BALL_RADIUS*3, int(self.y)-BALL_RADIUS*3))
        pygame.draw.circle(surf, col, (int(self.x), int(self.y)), BALL_RADIUS)
        for i in range(3):
            ang = self.spin + i * math.pi*2/3
            pygame.draw.arc(surf, (255,255,200),
                pygame.Rect(int(self.x)-BALL_RADIUS+2, int(self.y)-BALL_RADIUS+2, BALL_RADIUS*2-4, BALL_RADIUS*2-4),
                ang, ang+1.0, 2)


# ─── AI BRAIN ─────────────────────────────────────────────────────────────────
class AIDifficulty(Enum):
    EASY=0; MEDIUM=1; HARD=2; ELITE=3

class AIBrain:
    def __init__(self, diff: AIDifficulty = AIDifficulty.MEDIUM):
        self.diff = diff
        self.state = "idle"
        self.state_timer = 0.0
        self.think_timer = 0.0
        self.q_weights = {
            "idle":        {"chase_ball":0.7,"defend_goal":0.3},
            "chase_ball":  {"attack_goal":0.6,"defend_goal":0.3,"boost_hunt":0.1},
            "attack_goal": {"chase_ball":0.5,"defend_goal":0.3,"retreat":0.2},
            "defend_goal": {"chase_ball":0.6,"attack_goal":0.2,"boost_hunt":0.2},
            "retreat":     {"defend_goal":0.5,"chase_ball":0.4,"boost_hunt":0.1},
            "boost_hunt":  {"chase_ball":0.7,"attack_goal":0.3},
        }
        self.goals_conceded = 0; self.goals_scored = 0
        self.reaction_delay = [0.5,0.25,0.1,0.0][diff.value]
        self.aim_noise      = [30.0,15.0,6.0,1.0][diff.value]

    def adapt(self):
        diff = self.goals_scored - self.goals_conceded
        if diff < -2:
            self.aim_noise    = max(1.0, self.aim_noise - 3.0)
            self.reaction_delay = max(0.0, self.reaction_delay - 0.05)
        elif diff > 2:
            self.aim_noise    = min(40.0, self.aim_noise + 2.0)
            self.reaction_delay = min(0.6, self.reaction_delay + 0.03)

    def predict_ball(self, ball: Ball, steps=20, dt=0.05):
        px,py = ball.x,ball.y; pvx,pvy = ball.vx,ball.vy
        for _ in range(steps):
            px += pvx*dt; py += pvy*dt
        return px,py

    def choose_state(self, car: Car, ball: Ball, level_map: LevelMap):
        goal_x = SCREEN_W - GOAL_W//2
        ball_to_goal = abs(ball.x - goal_x)
        car_to_ball  = math.sqrt((car.x-ball.x)**2+(car.y-ball.y)**2)
        ball_danger  = ball.x > SCREEN_W*0.65 and ball_to_goal < 250
        boost_low    = car.boost < 30
        boost_near   = any(math.sqrt((car.x-p.x)**2+(car.y-p.y)**2)<200
                           for p in level_map.boost_pads if p.active)
        if ball_danger:                             return "defend_goal"
        if boost_low and boost_near:                return "boost_hunt"
        if car_to_ball < 150 and ball.x < SCREEN_W*0.5: return "attack_goal"
        weights = self.q_weights.get(self.state, self.q_weights["idle"])
        candidates = list(weights.keys())
        probs = np.array(list(weights.values())); probs /= probs.sum()
        return np.random.choice(candidates, p=probs)

    def get_controls(self, car: Car, ball: Ball, level_map: LevelMap, dt: float):
        self.think_timer -= dt; self.state_timer += dt
        if self.think_timer <= 0:
            self.state = self.choose_state(car, ball, level_map)
            self.think_timer = self.reaction_delay + random.uniform(-0.05,0.05)
        pred_bx,pred_by = self.predict_ball(ball)
        ai_goal_x = SCREEN_W - GOAL_W - 30
        player_goal_x = GOAL_W + 30
        if   self.state == "defend_goal":  tx = lerp(pred_bx,ai_goal_x,0.6); ty = lerp(pred_by,SCREEN_H//2,0.3)
        elif self.state == "attack_goal":  tx = pred_bx+(player_goal_x-pred_bx)*0.3; ty = pred_by
        elif self.state == "boost_hunt":
            nearest = None; nearest_d = 9999
            for pad in level_map.boost_pads:
                if pad.active:
                    d = math.sqrt((car.x-pad.x)**2+(car.y-pad.y)**2)
                    if d < nearest_d: nearest_d=d; nearest=pad
            tx,ty = (nearest.x,nearest.y) if nearest else (pred_bx,pred_by)
        elif self.state == "retreat":  tx,ty = ai_goal_x,SCREEN_H//2
        else:                          tx,ty = pred_bx,pred_by
        tx += random.uniform(-self.aim_noise,self.aim_noise)
        ty += random.uniform(-self.aim_noise,self.aim_noise)
        dx = tx-car.x; dy = ty-car.y
        ta = math.atan2(dy,dx)
        ad = (ta-car.angle+math.pi)%(math.pi*2)-math.pi
        left  = ad < -0.08; right = ad > 0.08
        dist  = math.sqrt(dx**2+dy**2)
        forward = dist > 40; back = False
        use_boost = car.boost>40 and dist>150 and self.state in ["attack_goal","defend_goal"]
        return left,right,forward,back,use_boost


# ─── GOAL ZONE ────────────────────────────────────────────────────────────────
class GoalZone:
    def __init__(self, side: str, level_cfg: dict):
        self.side  = side
        self.x     = 0 if side=="left" else SCREEN_W-GOAL_W
        self.y     = (SCREEN_H-GOAL_H)//2
        self.rect  = pygame.Rect(self.x,self.y,GOAL_W,GOAL_H)
        self.color = level_cfg["accent"] if side=="left" else level_cfg["accent2"]

    def check_goal(self, ball: Ball) -> bool:
        return self.rect.collidepoint(int(ball.x),int(ball.y))

    def draw(self, surf, t: float):
        pulse = 0.5 + 0.5*math.sin(t*2)
        gs = pygame.Surface((GOAL_W*5, GOAL_H+40), pygame.SRCALPHA)
        alpha = int(20+pulse*15)
        pygame.draw.rect(gs, (*self.color, alpha), (0,20,GOAL_W*5,GOAL_H))
        surf.blit(gs, (self.x-(GOAL_W*4 if self.side=="right" else 0), self.y-20))
        pygame.draw.rect(surf, self.color, self.rect, 3)
        for i in range(1,6):
            y = self.y + i*GOAL_H//6
            pygame.draw.line(surf, (*self.color, 60), (self.x,y), (self.x+GOAL_W,y), 1)


# ─── HUD ──────────────────────────────────────────────────────────────────────
def draw_hud(surf, fonts, player: Car, ai: Car, level_map: LevelMap,
             time_left: float, ai_state: str, particles: ParticleSystem,
             msg: str, msg_timer: float, combo: int):
    font_big, font_med, font_sm, font_xs = fonts
    cfg = level_map.cfg
    accent = cfg["accent"]
    accent2 = cfg["accent2"]

    # ── TOP BAR ──
    bar = pygame.Surface((SCREEN_W, 62), pygame.SRCALPHA)
    pygame.draw.rect(bar, (5,5,15,210), (0,0,SCREEN_W,62))
    pygame.draw.line(bar, (*accent, 80), (0,61),(SCREEN_W,61), 1)
    surf.blit(bar, (0,0))

    # Level name top-center
    lvl_txt = font_xs.render(f"◈  {cfg['name']}  ◈", True, accent)
    surf.blit(lvl_txt, (SCREEN_W//2 - lvl_txt.get_width()//2, 4))

    # Scores
    p_txt = font_big.render(str(player.score), True, accent)
    a_txt = font_big.render(str(ai.score),     True, accent2)
    surf.blit(p_txt, (SCREEN_W//2 - 80 - p_txt.get_width(), 14))
    surf.blit(a_txt, (SCREEN_W//2 + 80, 14))

    # Divider & timer
    pygame.draw.line(surf, (200,200,255), (SCREEN_W//2,12),(SCREEN_W//2,58), 2)
    t_col = (255,60,60) if time_left < 30 else (220,220,255)
    mins = int(time_left)//60; secs = int(time_left)%60
    t_txt = font_med.render(f"{mins}:{secs:02d}", True, t_col)
    surf.blit(t_txt, (SCREEN_W//2 - t_txt.get_width()//2, 16))

    # Combo
    if combo > 1:
        combo_txt = font_sm.render(f"COMBO x{combo}!", True, (255,220,0))
        surf.blit(combo_txt, (SCREEN_W//2 - combo_txt.get_width()//2, 64))

    # ── PLAYER BOOST BAR (bottom-left) ──
    _draw_boost(surf, fonts, 20, SCREEN_H-52, player.boost, "YOU", accent)

    # ── AI BOOST BAR (bottom-right) ──
    _draw_boost(surf, fonts, SCREEN_W-240, SCREEN_H-52, ai.boost, "AI", accent2)

    # ── AI STATE (top-right) ──
    ai_s = font_xs.render(f"AI▶ {ai_state.upper()}", True, (100,110,140))
    surf.blit(ai_s, (SCREEN_W - ai_s.get_width() - 14, 66))

    # ── HAZARD LEGEND (top-left) ──
    haz = cfg["description"]
    hz_txt = font_xs.render(haz, True, (80,90,120))
    surf.blit(hz_txt, (14, 66))

    # ── AI MESSAGE (bottom center) ──
    if msg and msg_timer > 0:
        alpha = min(255, int(msg_timer * 255))
        msg_s = font_sm.render(f"[ {msg} ]", True, (255,255,200))
        mx = SCREEN_W//2 - msg_s.get_width()//2
        pygame.draw.rect(surf, (5,5,15), (mx-8, SCREEN_H-84, msg_s.get_width()+16, 26))
        surf.blit(msg_s, (mx, SCREEN_H-84))

    # ── CONTROLS HINT ──
    ctrl = font_xs.render("WASD/↑↓←→  SPACE=BOOST  N=NEXT MAP  R=RESTART  ESC=QUIT", True, (55,60,80))
    surf.blit(ctrl, (SCREEN_W//2 - ctrl.get_width()//2, SCREEN_H-22))

def _draw_boost(surf, fonts, x, y, boost, label, color):
    font_sm = fonts[2]; font_xs = fonts[3]
    pygame.draw.rect(surf, (8,8,18), (x,y-18,220,46))
    lbl = font_xs.render(label, True, color)
    surf.blit(lbl, (x+4, y-16))
    pygame.draw.rect(surf, (25,25,40), (x,y,200,14), border_radius=4)
    fw = int(200 * boost / BOOST_MAX)
    bc = color if boost>30 else (255,60,60)
    if fw>0: pygame.draw.rect(surf, bc, (x,y,fw,14), border_radius=4)
    pygame.draw.rect(surf, color, (x,y,200,14), 1, border_radius=4)
    pct = font_xs.render(f"{int(boost)}%", True, (200,200,220))
    surf.blit(pct, (x+205, y))


# ─── LEVEL SELECT SCREEN ──────────────────────────────────────────────────────
def draw_level_select(surf, fonts, selected: int, t: float, best_scores: dict):
    font_big, font_med, font_sm, font_xs = fonts
    surf.fill((3,4,14))

    # Starfield
    rng = random.Random(99)
    for _ in range(200):
        sx,sy = rng.randint(0,SCREEN_W),rng.randint(0,SCREEN_H)
        sb = rng.randint(60,180)
        pulse = 0.5+0.5*math.sin(t*2+sx*0.1)
        sb2 = int(sb*pulse)
        pygame.draw.circle(surf,(sb2,sb2,sb2+30),(sx,sy),1)

    # Title
    title = font_big.render("COSMIC ROCKET LEAGUE", True, (0,220,255))
    sub   = font_sm.render("SELECT YOUR ARENA — USE ← → THEN ENTER", True, (80,90,140))
    surf.blit(title, (SCREEN_W//2-title.get_width()//2, 32))
    surf.blit(sub,   (SCREEN_W//2-sub.get_width()//2,  90))

    # Level cards
    card_w = 210; card_h = 300; spacing = 225
    total_w = len(LEVELS)*spacing - (spacing - card_w)
    start_x = SCREEN_W//2 - total_w//2

    for i, lvl in enumerate(LEVELS):
        cx = start_x + i*spacing
        cy = 160
        is_sel = (i == selected)

        # Card bg
        card = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
        alpha_bg = 200 if is_sel else 120
        pygame.draw.rect(card, (10,12,28,alpha_bg), (0,0,card_w,card_h), border_radius=10)
        col = lvl["accent"]
        border_w = 3 if is_sel else 1
        pulse2 = 0.5+0.5*math.sin(t*3) if is_sel else 0.5
        pygame.draw.rect(card, (*col, int(150+pulse2*105)), (0,0,card_w,card_h), border_w, border_radius=10)
        surf.blit(card, (cx, cy))

        # Level number
        num_txt = font_big.render(str(i+1), True, col if is_sel else (60,70,100))
        surf.blit(num_txt, (cx + card_w//2 - num_txt.get_width()//2, cy+18))

        # Name
        name_lines = lvl["name"].split(" ")
        for li, ln in enumerate(name_lines):
            nt = font_sm.render(ln, True, col if is_sel else (100,110,140))
            surf.blit(nt, (cx + card_w//2 - nt.get_width()//2, cy+75+li*26))

        # Subtitle
        sub2 = font_xs.render(lvl["subtitle"][:20], True, (80,90,120))
        surf.blit(sub2, (cx + card_w//2 - sub2.get_width()//2, cy+132))

        # Description bullets
        desc_lines = lvl["description"].split(" · ")
        for di,dl in enumerate(desc_lines[:3]):
            dt = font_xs.render(f"▸ {dl}", True, (70,80,110) if not is_sel else (140,160,180))
            surf.blit(dt, (cx+10, cy+165+di*22))

        # Best score
        best = best_scores.get(i, 0)
        bt = font_xs.render(f"BEST: {best}", True, (180,160,0) if best>0 else (40,45,60))
        surf.blit(bt, (cx + card_w//2 - bt.get_width()//2, cy+card_h-28))

        # Selected indicator
        if is_sel:
            arrow = font_med.render("▼ PRESS ENTER ▼", True, col)
            surf.blit(arrow, (cx + card_w//2 - arrow.get_width()//2, cy+card_h+12))

    pygame.display.flip()


# ─── AI MESSAGES ──────────────────────────────────────────────────────────────
AI_MSGS = {
    "goal_player": [
        "Nice shot! The portal bends to your will.",
        "Ball threaded through — clean strike!",
        "Goal! The cosmos acknowledges your aim.",
        "Lethal vector. AI defensive algorithm updating.",
    ],
    "goal_ai": [
        "AI intercept successful. Recalibrating.",
        "Defence miscalculated. Regroup immediately.",
        "AI scored. Boost reserves and push forward.",
        "The drone found the gap. Don't let it again.",
    ],
    "boost": [
        "Boost pad acquired. Maximum thrust online.",
        "Fuel reserves topped. Push the pace now.",
    ],
    "hazard": [
        "Hazard contact! Trajectory destabilised.",
        "Warning: anomaly interference detected.",
        "Field distortion — correct your heading!",
    ],
    "low_time": [
        "30 SECONDS REMAINING. Don't hold back.",
        "Final stretch. Every goal counts double.",
    ],
    "victory": ["🏆 MISSION COMPLETE. Galactic record updated."],
    "defeat":  ["💀 MISSION FAILED. AI wins this sector."],
    "draw":    ["⚖️  STALEMATE. The void remains unclaimed."],
}

def ai_say(category: str) -> str:
    msgs = AI_MSGS.get(category, ["..."])
    return random.choice(msgs)


# ─── GAME ─────────────────────────────────────────────────────────────────────
class Game:
    MATCH_TIME = 120.0

    def __init__(self):
        pygame.init()
        pygame.display.set_caption("🚀 COSMIC ROCKET LEAGUE — 5 Unique Arenas")
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        self.clock  = pygame.time.Clock()
        self.fonts  = (
            pygame.font.SysFont("consolas", 46, bold=True),
            pygame.font.SysFont("consolas", 30, bold=True),
            pygame.font.SysFont("consolas", 20, bold=True),
            pygame.font.SysFont("consolas", 15),
        )
        self.particles = ParticleSystem()
        self.best_scores = {i: 0 for i in range(len(LEVELS))}
        self.state     = "select"   # select | playing | goal_flash | gameover
        self.sel_level = 0
        self.t         = 0.0
        self._init_game(0)

    def _init_game(self, level_id: int):
        self.level_id  = level_id
        self.level_map = LevelMap(level_id)
        cfg = self.level_map.cfg
        self.player = Car(180, SCREEN_H//2, is_player=True,  level_cfg=cfg)
        self.ai_car = Car(SCREEN_W-180, SCREEN_H//2, is_player=False, level_cfg=cfg)
        self.ball   = Ball()
        self.goal_l = GoalZone("left",  cfg)
        self.goal_r = GoalZone("right", cfg)
        self.ai_brain = AIBrain(AIDifficulty.MEDIUM)
        self.ai_state = "idle"
        self.time_left = self.MATCH_TIME
        self.combo     = 1
        self.last_scorer = None
        self.flash_col = (255,255,255)
        self.flash_timer = 0.0
        self.msg       = ""
        self.msg_timer = 0.0
        self.low_time_warned = False
        self.winner    = None

    def reset_positions(self):
        self.player.x = 180;        self.player.y = SCREEN_H//2
        self.player.vx=0;           self.player.vy=0
        self.ai_car.x = SCREEN_W-180; self.ai_car.y = SCREEN_H//2
        self.ai_car.vx=0;           self.ai_car.vy=0
        self.ball.reset()
        self.player.trail.clear(); self.ai_car.trail.clear()

    def show_msg(self, category: str):
        self.msg = ai_say(category)
        self.msg_timer = 3.0

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if self.state == "select":
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        self.sel_level = (self.sel_level - 1) % len(LEVELS)
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        self.sel_level = (self.sel_level + 1) % len(LEVELS)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._init_game(self.sel_level)
                        self.state = "playing"
                    elif event.key == pygame.K_ESCAPE:
                        pygame.quit(); sys.exit()

                elif self.state == "playing":
                    if event.key == pygame.K_ESCAPE:
                        self.state = "select"
                    elif event.key == pygame.K_n:
                        self.sel_level = (self.sel_level+1)%len(LEVELS)
                        self._init_game(self.sel_level); self.state="playing"
                    elif event.key == pygame.K_r:
                        self._init_game(self.level_id); self.state="playing"

                elif self.state == "goal_flash":
                    if event.key == pygame.K_SPACE:
                        self.state = "playing"
                        self.reset_positions()

                elif self.state == "gameover":
                    if event.key == pygame.K_r:
                        self._init_game(self.level_id); self.state="playing"
                    elif event.key == pygame.K_n:
                        self.sel_level=(self.sel_level+1)%len(LEVELS)
                        self._init_game(self.sel_level); self.state="playing"
                    elif event.key == pygame.K_ESCAPE:
                        self.state = "select"

    def update(self, dt):
        self.t += dt
        self.msg_timer = max(0, self.msg_timer - dt)
        if self.flash_timer > 0: self.flash_timer -= dt

        if self.state != "playing": return

        # Controls
        keys = pygame.key.get_pressed()
        left    = keys[pygame.K_a] or keys[pygame.K_LEFT]
        right   = keys[pygame.K_d] or keys[pygame.K_RIGHT]
        forward = keys[pygame.K_w] or keys[pygame.K_UP]
        back    = keys[pygame.K_s] or keys[pygame.K_DOWN]
        boost   = keys[pygame.K_SPACE] or keys[pygame.K_LSHIFT]
        self.player.apply_input(left,right,forward,back,boost,dt)
        self.player.update(dt, self.level_map)

        # AI
        ai_l,ai_r,ai_f,ai_b,ai_boost = self.ai_brain.get_controls(
            self.ai_car, self.ball, self.level_map, dt)
        self.ai_state = self.ai_brain.state
        self.ai_car.apply_input(ai_l,ai_r,ai_f,ai_b,ai_boost,dt)
        self.ai_car.update(dt, self.level_map)

        # Ball
        self.ball.update(dt, self.level_map)
        self.ball.car_hit(self.player, self.particles)
        self.ball.car_hit(self.ai_car, self.particles)

        # Boost pad picked up message
        for pad in self.level_map.boost_pads:
            if not pad.active and pad.cooldown > 4.9:
                if self.msg_timer <= 0: self.show_msg("boost")

        # Hazard check
        if self.level_map.check_hazard_hit(self.player.x, self.player.y, max(CAR_W,CAR_H)//2):
            self.player.vx += random.uniform(-120,120)
            self.player.vy += random.uniform(-120,120)
            if self.msg_timer <= 0: self.show_msg("hazard")

        if self.player.boosting:
            self.particles.emit(self.player.x,self.player.y,0,0,
                                self.level_map.cfg["accent"],count=1,spread=5,life=0.2,size=3)

        # Goals
        if self.goal_l.check_goal(self.ball):
            self.ai_car.score += 1
            self.combo = 1
            self.ai_brain.goals_scored += 1; self.ai_brain.adapt()
            self._goal_event(self.level_map.cfg["accent2"], "goal_ai")
        elif self.goal_r.check_goal(self.ball):
            self.player.score += 1
            self.combo = min(self.combo+1, 8)
            self.ai_brain.goals_conceded += 1; self.ai_brain.adapt()
            self._goal_event(self.level_map.cfg["accent"], "goal_player")

        # Timer
        self.time_left -= dt
        if not self.low_time_warned and self.time_left < 30:
            self.show_msg("low_time"); self.low_time_warned=True
        if self.time_left <= 0:
            self.time_left = 0
            total = self.player.score + self.ai_car.score
            self.best_scores[self.level_id] = max(self.best_scores[self.level_id], total)
            if   self.player.score > self.ai_car.score: self.winner="player"; self.show_msg("victory")
            elif self.ai_car.score > self.player.score: self.winner="ai";     self.show_msg("defeat")
            else:                                        self.winner="draw";   self.show_msg("draw")
            self.state = "gameover"

        self.level_map.update(dt)
        self.particles.update(dt)

    def _goal_event(self, col, msg_cat):
        self.flash_col = col
        self.flash_timer = 1.2
        self.state = "goal_flash"
        self.show_msg(msg_cat)
        for _ in range(50):
            self.particles.emit(self.ball.x, self.ball.y, 0, 0, col,
                                count=3, spread=200, life=1.5, size=random.randint(3,8))

    def draw(self):
        if self.state == "select":
            draw_level_select(self.screen, self.fonts, self.sel_level, self.t, self.best_scores)
            return

        cfg = self.level_map.cfg
        self.screen.fill(cfg["bg"])
        self.level_map.draw(self.screen, self.t)

        # Field center line + circle
        accent = cfg["accent"]
        cx = SCREEN_W//2
        field_s = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        pygame.draw.line(field_s, (*accent, 40), (cx, 62), (cx, SCREEN_H), 1)
        pygame.draw.circle(field_s, (*accent, 30), (cx, SCREEN_H//2), 90, 1)
        pygame.draw.circle(field_s, (*accent, 50), (cx, SCREEN_H//2), 5)
        self.screen.blit(field_s, (0,0))

        self.goal_l.draw(self.screen, self.t)
        self.goal_r.draw(self.screen, self.t)
        self.particles.draw(self.screen)
        self.ball.draw(self.screen, cfg)
        self.player.draw(self.screen, self.particles)
        self.ai_car.draw(self.screen, self.particles)

        draw_hud(self.screen, self.fonts, self.player, self.ai_car,
                 self.level_map, self.time_left, self.ai_state,
                 self.particles, self.msg, self.msg_timer, self.combo)

        # Goal flash overlay
        if self.state == "goal_flash" and self.flash_timer > 0:
            ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            ov.fill((*self.flash_col, int(min(100, self.flash_timer * 80))))
            self.screen.blit(ov, (0,0))
            gt = self.fonts[1].render("GOAL!  PRESS SPACE", True, (255,255,255))
            self.screen.blit(gt, (SCREEN_W//2-gt.get_width()//2, SCREEN_H//2-20))

        # Gameover
        if self.state == "gameover":
            self._draw_gameover()

        pygame.display.flip()

    def _draw_gameover(self):
        ov = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        ov.fill((*self.level_map.cfg["bg"], 210))
        self.screen.blit(ov, (0,0))
        font_big, font_med, font_sm, font_xs = self.fonts
        cfg = self.level_map.cfg
        cx = SCREEN_W//2

        if   self.winner == "player": msg,col = "MISSION COMPLETE",   cfg["accent"]
        elif self.winner == "ai":     msg,col = "MISSION FAILED",      cfg["accent2"]
        else:                         msg,col = "DIMENSION STALEMATE", (200,200,200)

        t1 = font_big.render(msg, True, col)
        t2 = font_med.render(f"YOU  {self.player.score}  —  {self.ai_car.score}  AI", True, (220,220,255))
        t3 = font_sm.render(f"R = Restart   N = Next Map   ESC = Level Select", True, (80,90,120))
        ai_info = font_xs.render(
            f"AI adapted:  accuracy noise={self.ai_brain.aim_noise:.1f}  reaction={self.ai_brain.reaction_delay:.2f}s",
            True, (60,80,120))
        map_info = font_xs.render(
            f"Arena: {cfg['name']}  |  Anomalies: {len(self.level_map.anomalies)}  |  "
            f"Asteroids: {len(self.level_map.asteroids)}  |  Hazards: {', '.join(cfg['hazards']) or 'none'}",
            True, (50,60,90))
        best = font_xs.render(f"Total goals this match: {self.player.score + self.ai_car.score}", True, (150,140,0))

        self.screen.blit(t1,      (cx - t1.get_width()//2,      SCREEN_H//2-130))
        self.screen.blit(t2,      (cx - t2.get_width()//2,      SCREEN_H//2-68))
        self.screen.blit(t3,      (cx - t3.get_width()//2,      SCREEN_H//2+10))
        self.screen.blit(ai_info, (cx - ai_info.get_width()//2, SCREEN_H//2+50))
        self.screen.blit(map_info,(cx - map_info.get_width()//2, SCREEN_H//2+80))
        self.screen.blit(best,    (cx - best.get_width()//2,    SCREEN_H//2+108))

        if self.msg:
            msg_t = font_sm.render(self.msg, True, col)
            self.screen.blit(msg_t, (cx - msg_t.get_width()//2, SCREEN_H//2+148))

    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)
            self.handle_events()
            self.update(dt)
            self.draw()


# ─── ENTRY POINT ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    try:
        import numpy as np
        print("✅  NumPy loaded — AI Q-brain active")
    except ImportError:
        print("❌  NumPy required: pip install numpy")
        sys.exit(1)

    print("🚀  COSMIC ROCKET LEAGUE v2 — 5 Unique Arenas")
    print("    Levels: Lunar Colosseum · Nebula Rift · Asteroid Graveyard · Black Hole Station · Pulsar Core")
    print("    Controls: WASD/Arrows + SPACE=boost | N=next map | R=restart | ESC=level select")

    Game().run()
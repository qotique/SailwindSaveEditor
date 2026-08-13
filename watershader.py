#!/usr/bin/env python3
"""Animated wind-waker-style water "shader" that blends into the current theme.

Direct numpy port of the fbm noise band-mapping from flytrap's
"2D Procedural Water" godot shader
(https://godotshaders.com/shader/perlin-procedural-water/): layered fbm
value-noise sampled on animated UV offsets, with two threshold bands drawn
as an overlay -- light "crest" lines and darker "shadow" lines -- on top of
the theme's background color, so the sea keeps the theme's look.
Rendered at low resolution and nearest-upscaled so the waves keep the
chunky, pixel-snapped look of the scaled UI.
"""

try:
    import numpy as _np
except Exception:
    _np = None

import pygame

_BASE = (24, 26, 36)
_LINE = (244, 240, 255)


def _darken(color, amount=0.35):
    f = 1.0 - amount
    return tuple(max(0, min(255, int(round(c * f)))) for c in color)


class WaterShader:
    """Vectorized animated water. render() returns a fresh surface per frame."""

    def __init__(self):
        self._t = 0.0
        self._grid_cache = {}

    def _grids(self, w, h):
        key = (w, h)
        grids = self._grid_cache.get(key)
        if grids is None:
            if w <= 0 or h <= 0:
                return None
            ys, xs = _np.mgrid[0:h, 0:w].astype(_np.float32)
            grids = (xs / max(1, w), ys / max(1, h))
            self._grid_cache[key] = grids
        return grids

    @staticmethod
    def _rand(x, y):
        return (_np.sin(x * 23.53 + y * 44.0) * 42350.45) % 1.0

    @classmethod
    def _perlin(cls, x, y):
        i = _np.floor(x)
        j = _np.floor(y)
        fx = x - i
        fy = y - j
        u = fx * fx * (3.0 - 2.0 * fx)
        v = fy * fy * (3.0 - 2.0 * fy)
        a = cls._rand(i, j)
        b = cls._rand(i + 1, j)
        c = cls._rand(i, j + 1)
        d = cls._rand(i + 1, j + 1)
        return a * (1.0 - u) * (1.0 - v) + b * u * (1.0 - v) + c * (1.0 - u) * v + d * u * v

    @classmethod
    def _fbm(cls, x, y, octaves=4):
        acc = _np.zeros_like(x)
        amp = 0.5
        for _ in range(octaves):
            acc += cls._perlin(x, y) * amp
            x = x * 2.0
            y = y * 2.0
            amp *= 0.5
        return acc

    def render(self, width, height, dt, base=(24, 26, 36), line=(244, 240, 255), shadow=None):
        """Return a surface with grid/shadow bands drawn over the base color."""
        if _np is None or width <= 0 or height <= 0:
            return None
        base = tuple(base)
        line = tuple(line)
        shadow = tuple(shadow) if shadow is not None else _darken(base)
        self._t += dt

        lx = (width + 3) // 4
        ly = (height + 3) // 4
        grids = self._grids(lx, ly)
        if grids is None:
            return None
        u, v = grids
        t = self._t

        mul = 5.0
        foam = 0.1
        h0 = 0.6
        tide = 0.1

        fbmval = self._fbm(
            u * mul + 0.2 * _np.sin(0.3 * t) + 0.15 * t,
            v * mul + 0.1 * _np.cos(0.68 * t) - 0.05 * t,
        )
        fbmvalshadow = (
            self._fbm(
                u * mul + 0.2 * _np.sin(-0.6 * t + 25.0 * v) + 0.15 * t + 3.0,
                v * mul + 0.13 * _np.cos(-0.68 * t) - 0.05 * t,
            )
            + 0.1 * _np.sin(0.43 * t)
        )

        myheight = h0 + tide * _np.sin(t + 5.0 * u - 8.0 * v)
        shadowheight = h0 + tide * 1.3 * _np.cos(t + 2.0 * u - 2.0 * v)

        within_foam = (fbmval >= myheight) & (fbmval <= myheight + foam)
        shadow_mask = (
            (~within_foam)
            & (fbmvalshadow >= shadowheight)
            & (fbmvalshadow <= shadowheight + foam * 0.7)
        )

        rgb = _np.empty((ly, lx, 3), dtype=_np.float32)
        rgb[...] = base
        rgb[within_foam] = line
        rgb[shadow_mask] = shadow

        rgb = _np.repeat(_np.repeat(rgb, 4, axis=0), 4, axis=1)
        rgb = rgb[:height, :width]
        rgb = _np.clip(rgb, 0.0, 255.0).astype(_np.uint8)
        return pygame.image.frombuffer(rgb.tobytes(), (width, height), "RGB")
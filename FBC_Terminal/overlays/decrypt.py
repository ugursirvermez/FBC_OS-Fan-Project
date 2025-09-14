# -*- coding: utf-8 -*-
import random, math, pygame
from ..settings import FG, ACCENT, MUTED, BORDER, LOGO_PATH
from ..utils.audio import make_beep_sequence

class DecryptOverlay:
    """Kısa süreli 'Decrypting…' animasyonu; bitince on_done() çağırır."""
    GLYPHS = list("01▮▯▌▐░▒▓/\\-_|<>#*+$@ABCDEF")

    def __init__(self, app, duration=1.8, on_done=None):
        self.app = app
        self.duration = duration
        self.t = 0.0
        self.on_done = on_done

        self.font_big   = pygame.font.SysFont("consolas,monospace", 36, bold=True)
        self.font_med   = pygame.font.SysFont("consolas,monospace", 22, bold=True)
        self.font_small = pygame.font.SysFont("consolas,monospace", 16)

        self.noise_phase = 0.0
        self.progress = 0.0

        # logo
        self.logo = pygame.image.load(LOGO_PATH).convert_alpha()
        h = self.app.screen.get_height() // 3
        scale = h / self.logo.get_height()
        w = int(self.logo.get_width() * scale)
        self.logo = pygame.transform.smoothscale(self.logo, (w, h))

        w, h = self.app.screen.get_size()
        self.columns = max(24, w // 16)
        self.rows    = max(10, h // 18)
        self.drops   = [random.randint(-self.rows, 0) for _ in range(self.columns)]

        try: make_beep_sequence(count=3, beep_ms=60, pause_ms=60, freq=820, volume=0.20).play()
        except Exception: pass

    def update(self, dt):
        self.t += dt
        self.noise_phase += dt * 3.0
        self.progress = min(1.0, self.t / self.duration)

        for i in range(self.columns):
            if random.random() < 0.2:
                self.drops[i] += 1
            if self.drops[i] > self.rows:
                self.drops[i] = random.randint(-self.rows//2, 0)

        if self.t >= self.duration:
            try: make_beep_sequence(count=1, beep_ms=100, pause_ms=0, freq=980, volume=0.22).play()
            except Exception: pass
            if self.on_done:
                cb = self.on_done; self.on_done = None; cb()
            self.app.active_overlay = None

    def _draw_scan(self, s):
        w, h = s.get_size()
        line = pygame.Surface((w, 2), pygame.SRCALPHA)
        line.fill((0, 30, 0, 70))
        y = int((math.sin(self.noise_phase*1.6) * 0.5 + 0.5) * (h - 2))
        s.blit(line, (0, y))

    def _draw_noise(self, s):
        w, h = s.get_size()
        noise = pygame.Surface((w, h), pygame.SRCALPHA)
        a = int(18 + 8*math.sin(self.noise_phase*2.2))
        noise.fill((0, 255, 0, a))
        s.blit(noise, (0,0), special_flags=pygame.BLEND_RGBA_MULT)

    def _draw_matrix(self, s):
        w, h = s.get_size()
        col_w = max(8, w // self.columns)
        for x in range(self.columns):
            y_drop = self.drops[x]
            for y in range(y_drop):
                if 0 <= y < self.rows:
                    ch = random.choice(self.GLYPHS)
                    shadow = self.font_small.render(ch, True, (0,50,0))
                    s.blit(shadow, (x*col_w+1, y*18+1))
                    glyph = self.font_small.render(ch, True, ACCENT)
                    s.blit(glyph, (x*col_w, y*18))

    def _draw_progress(self, s):
        w, h = s.get_size()
        bar_w = int(w * 0.5); bar_h = 14
        rect = pygame.Rect(0,0,bar_w,bar_h); rect.center = (w//2, int(h*0.72))
        pygame.draw.rect(s, (20,60,20), rect, 1)
        fill = rect.copy(); fill.width = max(2, int(rect.width * self.progress))
        pygame.draw.rect(s, ACCENT, fill)
        label = self.font_med.render(f"DECRYPTING…  {int(self.progress*100):3d}%", True, FG)
        s.blit(label, (rect.centerx - label.get_width()//2, rect.top - 26))

    def draw(self, s):
        cover = pygame.Surface(s.get_size(), pygame.SRCALPHA); cover.fill((0, 20, 0, 180))
        s.blit(cover, (0,0))
        self._draw_noise(s); self._draw_matrix(s); self._draw_scan(s)
        overlay = pygame.Surface(s.get_size(), pygame.SRCALPHA); overlay.fill((0,0,0,160))
        s.blit(overlay, (0,0))
        rect = self.logo.get_rect(center=(s.get_width()//2, s.get_height()//2))
        s.blit(self.logo, rect)
        self._draw_progress(s)
        tip = self.font_small.render("Decrypting secure channel…", True, MUTED)
        s.blit(tip, (12, s.get_height()-26))

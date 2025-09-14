# -*- coding: utf-8 -*-
import random, pygame
from ..settings import FG, ACCENT, MUTED, BORDER, BG, TITLE_TEXT
from ..utils.audio import make_beep_sequence

SECTORS = [
    "Executive", "Maintenance", "Research", "Containment",
    "Black Rock Quarry", "NSC", "Panopticon", "Ashtray Maze",
]

ICONS = ["▲","■","●","◆","✦","✹","✱","✖"]

class ThresholdOverlay:
    """
    Kısa uyarı kartı; ekranda rastgele konumda 1.8–3.0 sn görünür, kendi kendine kapanır.
    """
    def __init__(self, app, text=None, icon=None, duration=None, pos=None):
        self.app = app
        self.text = text or "THRESHOLD ACTIVITY SPIKE DETECTED"
        self.icon = icon or random.choice(ICONS)
        self.duration = duration or random.uniform(1.8, 3.0)
        self.t = 0.0
        self.font_head  = pygame.font.SysFont("consolas,monospace", 22, bold=True)
        self.font_body  = pygame.font.SysFont("consolas,monospace", 18)
        self.font_small = pygame.font.SysFont("consolas,monospace", 14)

        # konum
        w, h = self.app.screen.get_size()
        panel_w, panel_h = 460, 120
        if pos is None:
            x = random.randint(20, max(22, w - panel_w - 22))
            y = random.randint(90, max(92, h - 220 - panel_h))
        else:
            x, y = pos
        self.rect = pygame.Rect(x, y, panel_w, panel_h)

        try: make_beep_sequence(count=3, beep_ms=70, pause_ms=70, freq=920, volume=0.22).play()
        except Exception: pass

        # sahte detaylar
        self.sector = random.choice(SECTORS)
        self.level  = random.choice(["LOW","MEDIUM","HIGH","CRITICAL"])

    def update(self, dt):
        self.t += dt
        if self.t >= self.duration:
            self.app.active_overlay = None  # kendini kapat
    
    def draw(self, s):
        w,h = s.get_size()
        veil = pygame.Surface((w,h), pygame.SRCALPHA)
        # varyant rengi seç: RED/GREEN/YELLOW vs.
        r,g,b = self.tint  # örn (220,40,40) veya (80,220,80) gibi
        veil.fill((r//4, g//4, b//4, 180))  # yarı saydam
        s.blit(veil, (0,0))
        # büyük başlık
        title_font = pygame.font.SysFont("consolas,monospace", 64, bold=True)
        s.blit(title_font.render(self.title, True, (r,g,b)), title_font.render(self.title, True, (r,g,b)).get_rect(center=(w//2, h//2 - 40)))
        # alt açıklama
        info_font = pygame.font.SysFont("consolas,monospace", 22)
        msg = info_font.render(self.message, True, ACCENT)
        s.blit(msg, msg.get_rect(center=(w//2, h//2 + 20)))

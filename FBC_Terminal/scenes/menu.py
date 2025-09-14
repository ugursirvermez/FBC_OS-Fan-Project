import pygame
from ..settings import BG, FG, ACCENT, MUTED, BORDER, TITLE_TEXT, LOGO_PATH
from ..utils.gfx import draw_text, draw_header_with_right_logo, draw_pulsing_highlight
from ..utils.text import warning_ascii_lines
from ..core.scene import *
from .docs import DocsList
from .videos import VideosList
from .audios import AudioLogsList
from .maps import MapsList
from .altered_items import AlteredList
from .quarry import QuarryScene
from .oop import OOPList
from ..overlays.threshold import ThresholdOverlay
from .hotline import HotlineScene

class MenuScene:
    """
    İlk çalışan menü. İçerik sahneleri henüz eklenmediği için
    seçimlerde “Coming next stage” uyarısı gösterir.
    """
    ITEMS = [
        "Documents",
        "Videos",
        "Audio Logs",
        "Altered Items",
        "Objects of Power",
        "Black Rock Quarry",
        "The Oldest House Sectors",
        "Hotline Chamber",
        "Oceanview Motel & Casino",
        "Quit",
    ]

    def __init__(self, app):
        self.app = app

    def enter(self):
        self.sel = 0
        self.scroll_x = None
        self.warning_lines = warning_ascii_lines("WARNING!")
        self.guide_lines = [
            "FBC OS — Quick Manual",
            "• Navigation: ↑/↓ move, Enter select, ESC back/quit",
            "• Fullscreen: F11",
            "• Documents: Enter open, ←/→ page, +/- zoom, 0 reset",
            "• Videos: Enter play, SPACE pause, F fit mode",
            "• Audio Logs: SPACE play/pause, ←/→ seek ±5s, click word to seek\n",
            " ",
            ]

    def exit(self):
        pass

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_w):
                self.sel = (self.sel - 1) % len(self.ITEMS)
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.sel = (self.sel + 1) % len(self.ITEMS)
            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self.activate()
            elif e.key in (pygame.K_ESCAPE, pygame.K_q):
                self.app.running = False
            elif e.key == pygame.K_F11:
                self.app.toggle_fullscreen()

    def update(self, dt):
        if self.scroll_x is None:
            self.scroll_x = self.app.screen.get_width()
        self.scroll_x -= 100 * dt

    def draw(self, s):
        if self.scroll_x is None:
            self.scroll_x = s.get_width()

        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )
        draw_text(s, "↑/↓ navigate • Enter select • ESC quit • F11 fullscreen",
                  18, MUTED, topleft=(content.left, content.top - 20))

        # Menu Content
        y0 = content.top + 8
        t = pygame.time.get_ticks() / 1000.0
        pulse = 60 + int(60 * (0.5 + 0.5 * (pygame.math.sin(t * 6) if hasattr(pygame.math, 'sin') else __import__('math').sin(t * 6))))
        item_h = 38; bar_w = 420

        for i, label in enumerate(self.ITEMS):
            y_pos = y0 + i * 46
            if i == self.sel:
                rect = pygame.Rect(content.left - 10, y_pos - 4, bar_w, item_h)
                draw_pulsing_highlight(s, rect, pulse)
                draw_text(s, "▸", 28, FG, topleft=(content.left - 6, y_pos)); color = FG
            else:
                color = ACCENT
            draw_text(s, f"[ {label} ]", 28, color, topleft=(content.left + 18, y_pos))
        #MANUAL
        lines = self.guide_lines
        line_font = pygame.font.SysFont("consolas,monospace", 20, bold=False)
        title_font = pygame.font.SysFont("consolas,monospace", 22, bold=True)
        
        # Header Helper on box
        box_left  = content.left - 10
        box_right = content.right  # header helper 
        inner_pad = 10
        line_h    = line_font.get_height() + 4
        box_h     = inner_pad*2 + (len(lines)-1)*line_h + title_font.get_height()
        box_top   = y0 + len(self.ITEMS)*46 + 16  # after the menu

        warning_top = s.get_height() - 200
        if box_top + box_h > warning_top - 10:
            box_h = max(42, (warning_top - 10) - box_top)

        guide_rect = pygame.Rect(box_left, box_top, box_right - box_left, box_h)

        panel = pygame.Surface((guide_rect.width, guide_rect.height), pygame.SRCALPHA)
        panel.fill((0, 30, 0, 120))
        s.blit(panel, guide_rect.topleft)
        pygame.draw.rect(s, BORDER, guide_rect, 1)

        tx = guide_rect.left + inner_pad
        ty = guide_rect.top  + inner_pad
        title_surf = title_font.render(lines[0], True, FG)
        s.blit(title_surf, (tx, ty)); ty += title_font.get_height() + 2
        for ln in lines[1:]:
            s.blit(line_font.render(ln, True, ACCENT), (tx, ty))
            ty += line_h
            
        # --- Blinking ASCII WARNING (red) ---
        t = pygame.time.get_ticks() / 1000.0
        blink_on = (int(t * 2) % 2) == 0
        if blink_on:
            base_y = s.get_height() - 200  
            font22 = pygame.font.SysFont("consolas,monospace", 22, bold=True)
            for i, line in enumerate(self.warning_lines):  # self.warning_lines: enter() -> warning_ascii_lines("WARNING!")
                # black outline
                s.blit(font22.render(line, True, (0,0,0)), (40+2, base_y + i*22 + 2))
                # Red warning
                s.blit(font22.render(line, True, (200,20,20)), (40,   base_y + i*22))

        # Warning Message
        msg = ("Due to the Hiss attack, The Oldest House has been locked down. "
               "Until further orders, no one is to leave their post. "
               "Secure the Black Rock and Central Executive units. "
               "Pay attention to the Northmoore facility.")
        font = pygame.font.SysFont("consolas,monospace", 22, bold=True)
        txt_surf = font.render(msg, True, ACCENT)
        ypos = s.get_height() - 60
        if self.scroll_x + txt_surf.get_width() < 0:
            self.scroll_x = s.get_width()
        s.blit(txt_surf, (int(self.scroll_x), ypos))

    # --- helpers ---

    def activate(self):
        item = self.ITEMS[self.sel]
        if item == "Documents":
            self.app.scenes.switch(DocsList)
        elif item == "Videos":
            self.app.scenes.switch(VideosList)
        elif item == "Audio Logs":
            self.app.scenes.switch(AudioLogsList)
        elif item == "Maps":
            self.app.scenes.switch(MapsList)
        elif item == "Altered Items":
            self.app.scenes.switch(AlteredList)
        elif item == "Objects of Power":
            self.app.scenes.switch(OOPList)
        elif item == "Black Rock Quarry":
            self.app.scenes.switch(QuarryScene)
        elif item == "The Oldest House Sectors":
            self.app.scenes.switch(MapsList)
        elif item == "Hotline Chamber":
            self.app.scenes.switch(HotlineScene)
        elif item == "Oceanview Motel & Casino":
            self.app.run_oceanview()
        elif item == "Quit":
            self.app.running = False

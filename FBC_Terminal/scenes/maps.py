# -*- coding: utf-8 -*-
import os, pygame

from ..settings import (
    BG, FG, ACCENT, MUTED, BORDER,
    TITLE_TEXT, LOGO_PATH, MAPS_DIR
)
from ..core.scene import Scene
from ..utils.gfx import draw_text, draw_header_with_right_logo, draw_pulsing_highlight

# ---------------- helpers ----------------
def _list_maps():
    if not os.path.isdir(MAPS_DIR):
        return []
    out = []
    for n in sorted(os.listdir(MAPS_DIR)):
        if n.lower().endswith(".png"):
            out.append(os.path.join(MAPS_DIR, n))
    return out

def _load_thumb(path, max_w=440, max_h=280):
    """Small thumbnail; returns Surface or None."""
    try:
        img = pygame.image.load(path).convert()
        w, h = img.get_width(), img.get_height()
        scale = min(max_w / w, max_h / h, 1.0)
        nw, nh = max(1, int(w*scale)), max(1, int(h*scale))
        return pygame.transform.smoothscale(img, (nw, nh))
    except Exception:
        return None


# ---------------- list scene ----------------
class MapsList(Scene):
    def enter(self):
        self.files = _list_maps()
        self.sel = 0
        self.thumb_cache = {}  # path -> Surface
        self.line_h = pygame.font.SysFont("consolas,monospace", 24).get_height() + 6

        if not self.files:
            self.app.push_info(f'Put .png maps in "{MAPS_DIR}"')

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                from .menu import MenuScene
                self.app.scenes.switch(MenuScene)
            elif self.files:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = (self.sel - 1) % len(self.files)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = (self.sel + 1) % len(self.files)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    idx = self.sel
                    files_copy = list(self.files)  # aktar
                    self.app.scenes.switch(lambda app: MapViewerScene(app, files_copy, idx))
                elif e.key == pygame.K_F11:
                    self.app.toggle_fullscreen()

    def _thumb(self, path):
        s = self.thumb_cache.get(path)
        if s: return s
        s = _load_thumb(path)
        if s:
            self.thumb_cache[path] = s
        return s

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )
        draw_text(s, f"The Oldest House Maps  ({len(self.files)} items)",
                  22, FG, topleft=(content.left, content.top - 8))
        draw_text(s, "Enter: open • ↑/↓ select • F11 fullscreen • ESC back",
                  18, MUTED, topleft=(content.left, content.top + 20))

        import math
        t = pygame.time.get_ticks()/1000.0
        pulse = 60 + int(60*(0.5 + 0.5*math.sin(t*6)))

        y0 = content.top + 48
        area_h = content.bottom - y0
        max_lines = max(1, area_h // self.line_h)
        start = max(0, self.sel - max_lines // 2)
        end   = min(len(self.files), start + max_lines)

        # list
        y = y0
        for i in range(start, end):
            p = self.files[i]
            name = os.path.splitext(os.path.basename(p))[0].replace("_"," ").title()
            if i == self.sel:
                rect = pygame.Rect(content.left - 8, y - 2, content.width + 8, self.line_h)
                draw_pulsing_highlight(s, rect, pulse)
                draw_text(s, "▸", 24, FG, topleft=(content.left - 4, y))
                color = FG
            else:
                color = ACCENT
            draw_text(s, name, 24, color, topleft=(content.left + 18, y))
            y += self.line_h

        # preview panel (below list)
        if self.files:
            sel_path = self.files[self.sel]
            thumb = self._thumb(sel_path)
            if thumb:
                panel_h = thumb.get_height() + 20
                panel_w = min(max(thumb.get_width()+20, 260), content.width)
                panel_y = y0 + min(len(self.files), max_lines)*self.line_h + 16
                panel_rect = pygame.Rect(content.left - 8, panel_y, panel_w, panel_h)

                bottom_guard = s.get_height() - 210  # WARNING
                if panel_rect.bottom > bottom_guard:
                    panel_rect.bottom = bottom_guard

                panel = pygame.Surface((panel_rect.width, panel_rect.height), pygame.SRCALPHA)
                panel.fill((0,30,0,120))
                pygame.draw.rect(panel, BORDER, panel.get_rect(), 1)
                # center thumb
                r = thumb.get_rect(center=panel.get_rect().center)
                panel.blit(thumb, r)
                s.blit(panel, panel_rect.topleft)


# ---------------- viewer scene ----------------
class MapViewerScene(Scene):
    """
    Fit modları: 0=fit both, 1=fit width, 2=fit height, 3=free zoom
    Pan: ok tuşları
    """
    def __init__(self, app, files, index):
        super().__init__(app)
        self.files = files
        self.index = index
        self.base = None
        self.img = None
        self.scale = 1.0
        self.fit_mode = 0
        self.offset = [0, 0]

    def enter(self):
        self._load_current()

    def _load_current(self):
        if not self.files:
            from .maps import MapsList
            self.app.push_info("No map.")
            self.app.scenes.switch(MapsList)
            return
        self.index %= len(self.files)
        path = self.files[self.index]
        try:
            self.base = pygame.image.load(path).convert()
        except Exception:
            from .maps import MapsList
            self.app.push_info("Cannot load image.")
            self.app.scenes.switch(MapsList)
            return
        self._auto_fit()

    def _auto_fit(self):
        sw, sh = self.app.screen.get_size()
        iw, ih = self.base.get_width(), self.base.get_height()
        tw, th = int(sw*0.9), int(sh*0.82)
        if self.fit_mode == 1:
            scale = tw / iw
        elif self.fit_mode == 2:
            scale = th / ih
        else:
            scale = min(tw/iw, th/ih)
        self.scale = max(0.05, scale)
        self._rebuild_image()
        self.offset = [0, 0]

    def _rebuild_image(self):
        iw, ih = self.base.get_width(), self.base.get_height()
        nw, nh = max(1, int(iw*self.scale)), max(1, int(ih*self.scale))
        self.img = pygame.transform.smoothscale(self.base, (nw, nh))

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                from .maps import MapsList
                self.app.scenes.switch(MapsList)
            elif e.key in (pygame.K_LEFT, pygame.K_a):
                self.index = (self.index - 1) % len(self.files); self._load_current()
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % len(self.files); self._load_current()
            elif e.key == pygame.K_f:
                self.fit_mode = (self.fit_mode + 1) % 3; self._auto_fit()
            elif e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.scale *= 1.10; self._rebuild_image()
            elif e.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                self.scale *= 0.90; self._rebuild_image()
            elif e.key == pygame.K_0:
                self._auto_fit()
            elif e.key == pygame.K_UP:
                self.offset[1] += 20
            elif e.key == pygame.K_DOWN:
                self.offset[1] -= 20
            elif e.key == pygame.K_LEFT:
                self.offset[0] += 20
            elif e.key == pygame.K_RIGHT:
                self.offset[0] -= 20

    def update(self, dt): pass

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )

        if self.img:
            rect = self.img.get_rect()
            cx = s.get_width()//2 + self.offset[0]
            cy = int(s.get_height()*0.53) + self.offset[1]
            rect.center = (cx, cy)
            s.blit(self.img, rect)

        name = os.path.basename(self.files[self.index]) if self.files else "-"
        draw_text(s, f"Map: {name}   [{self.index+1}/{len(self.files)}]   Zoom: {self.scale*100:.0f}%",
                  18, MUTED, topleft=(content.left, content.top - 20))
        draw_text(s, "←/→ next/prev • +/- zoom • 0 fit • F fit mode • ESC back",
                  18, MUTED, topleft=(content.left, content.bottom + 8))
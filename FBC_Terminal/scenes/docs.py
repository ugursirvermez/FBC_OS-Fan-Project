# -*- coding: utf-8 -*-
import os
import pygame

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None

from ..settings import BG, FG, MUTED, ACCENT, TITLE_TEXT, LOGO_PATH, PDF_PATH
from ..core.scene import Scene
from ..utils.gfx import draw_text, draw_header_with_right_logo, draw_pulsing_highlight

# --------- PDF helper ---------
class PDFDoc:
    def __init__(self, path):
        if fitz is None:
            raise RuntimeError("PyMuPDF (fitz) is not installed.")
        if not os.path.exists(path):
            raise FileNotFoundError(path)
        self.doc = fitz.open(path)
        self.n = self.doc.page_count
        self.titles = self._extract_titles()
        self._cache = {}         # key: (index, zoom_int) -> pygame.Surface
        self._lru_order = []     # for simple cache eviction

    def _extract_titles(self):
        out = []
        for i in range(self.doc.page_count):
            page = self.doc.load_page(i)
            txt = page.get_text("text") or ""
            lines = [l.strip() for l in txt.splitlines() if l.strip()]
            head = lines[0] if lines else f"Page {i+1}"
            head = head.replace("\u00A0", " ").strip()
            if len(head) > 100:
                head = head[:100] + "…"
            out.append(f"{i+1:03d} — {head}")
        return out

    def render_page_surface(self, index, screen_size, zoom=1.0):
        index = max(0, min(self.n - 1, index))
        key = (index, int(zoom * 100))
        if key in self._cache:
            # simple LRU refresh
            if key in self._lru_order:
                self._lru_order.remove(key)
            self._lru_order.insert(0, key)
            return self._cache[key]

        page = self.doc.load_page(index)
        sw, sh = screen_size
        pw, ph = page.rect.width, page.rect.height

        target_w, target_h = sw * 0.9, sh * 0.9
        base_scale = min(target_w / pw, target_h / ph)
        mat = fitz.Matrix(base_scale * zoom, base_scale * zoom)
        pix = page.get_pixmap(matrix=mat, alpha=False)
        surf = pygame.image.frombuffer(pix.samples, (pix.width, pix.height), "RGB").convert()

        self._cache[key] = surf
        self._lru_order.insert(0, key)
        while len(self._lru_order) > 6:
            old = self._lru_order.pop()
            self._cache.pop(old, None)
        return surf

# --------- Scenes ---------
class DocsList(Scene):
    """PDF sayfalarını başlıklarıyla listeler; Enter ile sayfayı açar."""
    def enter(self):
        try:
            self.pdf = PDFDoc(PDF_PATH)
            self.err = None
        except Exception as e:
            self.pdf = None
            self.err = str(e)

        self.sel = 0
        self.line_h = pygame.font.SysFont("consolas,monospace", 24).get_height() + 6

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                from .menu import MenuScene
                self.app.scenes.switch(MenuScene)
            elif self.pdf:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = max(0, self.sel - 1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = min(self.pdf.n - 1, self.sel + 1)
                elif e.key == pygame.K_PAGEUP:
                    self.sel = max(0, self.sel - 12)
                elif e.key == pygame.K_PAGEDOWN:
                    self.sel = min(self.pdf.n - 1, self.sel + 12)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    idx = self.sel
                    self.app.scenes.switch(lambda app: PageView(app, self.pdf, idx))
                elif e.key == pygame.K_F11:
                    self.app.toggle_fullscreen()

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.52, top_pad=36, side_pad=40
        )
        draw_text(s, "Documents (PDF)", 22, FG, topleft=(content.left, content.top - 8))
        draw_text(s, "Enter: open • ESC: back • PgUp/PgDn: fast scroll",
                  18, MUTED, topleft=(content.left, content.top + 20))

        if not self.pdf:
            draw_text(s, f"Cannot open PDF: {self.err}", 22, ACCENT,
                      topleft=(content.left, content.top + 60))
            return

        t = pygame.time.get_ticks() / 1000.0
        import math
        pulse = 60 + int(60 * (0.5 + 0.5 * math.sin(t * 6)))
        y = content.top + 48
        area_h = content.bottom - y
        max_lines = max(1, area_h // self.line_h)
        start = max(0, self.sel - max_lines // 2)
        end   = min(self.pdf.n, start + max_lines)

        for i in range(start, end):
            if i == self.sel:
                rect = pygame.Rect(content.left - 8, y - 2, content.width + 8, self.line_h)
                draw_pulsing_highlight(s, rect, pulse)
                draw_text(s, "▸", 24, FG, topleft=(content.left - 4, y))
                color = FG
            else:
                color = ACCENT
            draw_text(s, self.pdf.titles[i], 24, color, topleft=(content.left + 18, y))
            y += self.line_h

        draw_text(s, f"{self.sel+1}/{self.pdf.n}", 18, MUTED,
                  topleft=(content.left, content.bottom + 8))

class PageView(Scene):
    """Tek sayfa görüntüleyici: ←/→ sayfa, +/- zoom, 0 reset."""
    def __init__(self, app, pdf, index):
        super().__init__(app)
        self.pdf = pdf
        self.index = index
        self.zoom = 1.0
        self.surf = None

    def enter(self):
        self._update_surface()

    def _update_surface(self):
        self.surf = self.pdf.render_page_surface(self.index, self.app.screen.get_size(), self.zoom)

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                # Back to List
                self.app.scenes.switch(DocsList)
            elif e.key == pygame.K_RIGHT:
                self.index = min(self.pdf.n - 1, self.index + 1)
                self._update_surface()
            elif e.key == pygame.K_LEFT:
                self.index = max(0, self.index - 1)
                self._update_surface()
            elif e.key in (pygame.K_EQUALS, pygame.K_PLUS, pygame.K_KP_PLUS):
                self.zoom = min(3.0, self.zoom * 1.25)
                self._update_surface()
            elif e.key in (pygame.K_MINUS, pygame.K_UNDERSCORE, pygame.K_KP_MINUS):
                self.zoom = max(0.5, self.zoom / 1.25)
                self._update_surface()
            elif e.key == pygame.K_0:
                self.zoom = 1.0
                self._update_surface()
            elif e.key == pygame.K_F11:
                self.app.toggle_fullscreen()
        elif e.type == pygame.VIDEORESIZE:
            self._update_surface()

    def draw(self, s):
        s.fill(BG)
        w, h = s.get_size()
        if self.surf:
            rect = self.surf.get_rect(center=(w//2, h//2))
            s.blit(self.surf, rect)

        # Green overlay
        overlay = pygame.Surface(s.get_size()).convert_alpha()
        overlay.fill((0, 180, 0, 40))
        s.blit(overlay, (0, 0))

        title = self.pdf.titles[self.index]
        draw_text(s, title, 20, FG, topleft=(20, 14))
        draw_text(s, "←/→ page • +/- zoom • 0: reset • ESC: back", 18, MUTED, topleft=(20, 42))
        draw_text(s, f"{self.index+1}/{self.pdf.n}  zoom {self.zoom:.2f}x",
                  18, MUTED, topleft=(w - 240, 14))

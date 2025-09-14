# -*- coding: utf-8 -*-
import os, pygame, math
from ..settings import (
    BG, FG, ACCENT, MUTED, BORDER,
    TITLE_TEXT, LOGO_PATH, ALTERED_DIR
)
from ..core.scene import Scene
from ..utils.gfx import draw_text, draw_header_with_right_logo, draw_pulsing_highlight

def draw_stamp(surface, text="CLASSIFIED", color=(220,40,40), scale=1.0, angle=-18):
    font = pygame.font.SysFont("consolas,monospace", int(52*scale), bold=True)
    stamp = font.render(text, True, color)
    stamp = pygame.transform.rotate(stamp, angle)
    r = stamp.get_rect()
    r.center = (surface.get_width()//2, int(surface.get_height()*0.22))
    # gölge
    shadow = font.render(text, True, (0,0,0))
    shadow = pygame.transform.rotate(shadow, angle)
    surface.blit(shadow, r.move(2,2))
    surface.blit(stamp, r)

def _list_item_dirs(root):
    """Return [(folder_name, abs_path)] for folders in root."""
    if not os.path.isdir(root):
        return []
    out = []
    for n in sorted(os.listdir(root)):
        p = os.path.join(root, n)
        if os.path.isdir(p):
            out.append((n, p))
    return out

def _safe_load_text(path, default="(not available)"):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            t = f.read().strip()
            return t if t else default
    except Exception:
        return default

def _wrap_text_to_surface(surface, rect, text, font, color, line_gap=4, par_gap=8):
    """Word-wrap paragraphs inside rect."""
    x, y, w, h = rect
    max_y = y + h
    cur_y = y
    paragraphs = [p.strip() for p in text.replace("\r\n", "\n").split("\n\n")]
    for para in paragraphs:
        words = para.split()
        line_h = font.get_height()
        if not words:
            cur_y += line_h + par_gap
            if cur_y > max_y: break
            continue
        line_words = []
        for word in words:
            test = (" ".join(line_words + [word])) if line_words else word
            if font.size(test)[0] <= w:
                line_words.append(word)
            else:
                ln = " ".join(line_words)
                surface.blit(font.render(ln, True, color), (x, cur_y))
                cur_y += line_h + line_gap
                if cur_y > max_y: break
                line_words = [word]
        if cur_y > max_y: break
        if line_words:
            ln = " ".join(line_words)
            surface.blit(font.render(ln, True, color), (x, cur_y))
            cur_y += line_h + par_gap
        if cur_y > max_y: break
    if cur_y > max_y:
        ell = font.render("...", True, color)
        surface.blit(ell, (x, max_y - font.get_height()))
    return cur_y - y

# -------- list scene --------
class AlteredList(Scene):
    def enter(self):
        self.items = _list_item_dirs(ALTERED_DIR)
        self.sel = 0
        self.line_h = pygame.font.SysFont("consolas,monospace", 24).get_height() + 6
        if not self.items:
            self.app.push_info(f'Put item folders under "{ALTERED_DIR}"')

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                from .menu import MenuScene
                self.app.scenes.switch(MenuScene)
            elif self.items:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = (self.sel - 1) % len(self.items)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = (self.sel + 1) % len(self.items)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    name, path = self.items[self.sel]
                    self.app.scenes.switch(lambda app: AlteredDetail(app, name, path))
                elif e.key == pygame.K_F11:
                    self.app.toggle_fullscreen()

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )
        draw_text(s, "Altered Items", 22, FG, topleft=(content.left, content.top - 8))
        draw_text(s, "Enter: open • ↑/↓ select • ESC back", 18, MUTED,
                  topleft=(content.left, content.top + 20))

        EXTRA_DOWN = 40   # 32, 48-56 
        content.move_ip(0, EXTRA_DOWN)
        content.height = max(50, content.height - EXTRA_DOWN)

        t = pygame.time.get_ticks()/1000.0
        pulse = 60 + int(60*(0.5 + 0.5*math.sin(t*6)))

        y = content.top + 48
        area_h = content.bottom - y
        max_lines = max(1, area_h // self.line_h)
        start = max(0, self.sel - max_lines // 2)
        end   = min(len(self.items), start + max_lines)

        for i in range(start, end):
            label = self.items[i][0]
            if i == self.sel:
                rect = pygame.Rect(content.left - 8, y - 2, content.width + 8, self.line_h)
                draw_pulsing_highlight(s, rect, pulse)
                draw_text(s, "▸", 24, FG, topleft=(content.left - 4, y))
                color = FG
            else:
                color = ACCENT
            draw_text(s, label, 24, color, topleft=(content.left + 18, y))
            y += self.line_h
            draw_stamp(s, "CLASSIFIED", color=(220,40,40), scale=1.0, angle=-18)

# -------- detail scene --------
class AlteredDetail(Scene):
    def __init__(self, app, folder_name, folder_path):
        super().__init__(app)
        self.folder_name = folder_name
        self.folder_path = folder_path
        self.scroll_y = 0
        self.scroll_v = 28

        self.font_head  = pygame.font.SysFont("consolas,monospace", 22, bold=True)
        self.font_body  = pygame.font.SysFont("consolas,monospace", 18)
        self.font_small = pygame.font.SysFont("consolas,monospace", 14)

        self.img = None
        self.info_text  = "(not available)"
        self.dates_text = "(not available)"

    def enter(self):
        # load texts
        self.info_text  = _safe_load_text(os.path.join(self.folder_path, "info.txt"))
        self.dates_text = _safe_load_text(os.path.join(self.folder_path, "dates.txt"))

        # load optional image
        img_path = os.path.join(self.folder_path, "image.png")
        if os.path.exists(img_path):
            try:
                self.img = pygame.image.load(img_path).convert_alpha()
            except Exception:
                self.img = None

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                self.app.scenes.switch(AlteredList)
            elif e.key in (pygame.K_PAGEUP,):
                self.scroll_y = max(0, self.scroll_y - self.scroll_v*4)
            elif e.key in (pygame.K_PAGEDOWN,):
                self.scroll_y += self.scroll_v*4
            elif e.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - self.scroll_v)
            elif e.key == pygame.K_DOWN:
                self.scroll_y += self.scroll_v
            elif e.key == pygame.K_f:
                self.app.toggle_fullscreen()
        elif e.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - e.y*self.scroll_v)

    def update(self, dt): pass

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )
        draw_text(s, f"[Altered Item] {self.folder_name}", 20, FG,
                  topleft=(content.left, content.top - 8))
        draw_text(s, "PgUp/PgDn/↑↓ scroll • ESC back", 18, MUTED,
                  topleft=(content.left, content.top + 20))
        
        EXTRA_DOWN = 48  
        content.move_ip(0, EXTRA_DOWN)
        content.height = max(50, content.height - EXTRA_DOWN)
        # layout inside content: left text, right image
        full = s.get_rect()
        margin = 16
        left_w  = int(content.width * 0.64)
        right_w = int(content.width * 0.34)
        left_rect  = pygame.Rect(content.left - 10, content.top + 8, left_w, int(full.height * 0.72))
        right_rect = pygame.Rect(content.right - right_w, content.top + 8, right_w, int(full.height * 0.72))

        bottom_guard = full.height - 200
        left_rect.height  = min(left_rect.height,  bottom_guard - left_rect.top - margin)
        right_rect.height = min(right_rect.height, bottom_guard - right_rect.top - margin)

        # left panel (dates + info)
        panelL = pygame.Surface((left_rect.width, left_rect.height), pygame.SRCALPHA)
        panelL.fill((0, 30, 0, 120)); pygame.draw.rect(panelL, BORDER, panelL.get_rect(), 1)
        inner = pygame.Rect(12, 12, left_rect.width-24, left_rect.height-24)

        # scrollable canvas
        big_h = max(inner.height * 3, 6000)
        canvas = pygame.Surface((inner.width, big_h), pygame.SRCALPHA)
        y = 0
        # head: dates
        canvas.blit(self.font_head.render("Dates / Incidents", True, FG), (0, y)); y += self.font_head.get_height() + 6
        y += _wrap_text_to_surface(canvas, (0, y, inner.width, big_h - y), self.dates_text, self.font_body, ACCENT, 4, 10)
        y += 12
        # head: info
        canvas.blit(self.font_head.render("Details", True, FG), (0, y)); y += self.font_head.get_height() + 6
        y += _wrap_text_to_surface(canvas, (0, y, inner.width, big_h - y), self.info_text, self.font_body, FG, 4, 10)

        max_scroll = max(0, y - inner.height)
        if self.scroll_y > max_scroll: self.scroll_y = max_scroll
        view = pygame.Surface((inner.width, inner.height), pygame.SRCALPHA)
        view.blit(canvas, (0, -self.scroll_y))
        panelL.blit(view, (inner.left, inner.top))
        s.blit(panelL, left_rect.topleft)

        # right panel (image)
        panelR = pygame.Surface((right_rect.width, right_rect.height), pygame.SRCALPHA)
        panelR.fill((0, 30, 0, 120)); pygame.draw.rect(panelR, BORDER, panelR.get_rect(), 1)
        tx, ty = 10, 10
        panelR.blit(self.font_small.render("Image", True, FG), (tx, ty)); ty += 20
        if self.img:
            iw, ih = self.img.get_width(), self.img.get_height()
            max_w, max_h = right_rect.width-20, right_rect.height-40
            scale = min(max_w/iw, max_h/ih, 1.0)
            surf = pygame.transform.smoothscale(self.img, (int(iw*scale), int(ih*scale)))
            r = surf.get_rect(center=(right_rect.width//2, right_rect.height//2 + 10))
            panelR.blit(surf, r)
        else:
            panelR.blit(self.font_small.render("(no image)", True, MUTED), (tx, ty))
        s.blit(panelR, right_rect.topleft)
        draw_stamp(s, "TOP SECRET", color=(220,40,40), scale=1.0, angle=-18)


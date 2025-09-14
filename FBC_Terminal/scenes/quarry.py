# -*- coding: utf-8 -*-
import os, random, math, pygame
from ..core.scene import Scene
from ..settings import (
    BG, FG, ACCENT, MUTED, BORDER, TITLE_TEXT,
    QUARRY_ROWS, QUARRY_COLS, QUARRY_COOLDOWN
)
from ..utils.gfx import draw_text, draw_header_with_right_logo

# Tema renkleri
GREEN  = (90, 220, 120)
YELLOW = (225, 205, 80)
RED    = (210, 60, 60)
CYAN   = (120, 220, 220)

# ASCII dokular
CHAR_RICH    = "█"
CHAR_LIMITED = "▓"
CHAR_EMPTY   = "░"

class QuarryScene(Scene):
    """
    Black Rock Quarry — ASCII grid mini oyun (A–H x 1–12 varsayılan)
    - Ok tuşları / WASD ile hücre seç
    - [ / ] veya 1–9 ile miktar ayarla
    - Enter/Space ile çıkarım başlat (cooldown = drone anim süresi)
    - Hücreler ASCII doku + renk: Rich=█ (yeşil), Limited=▓ (sarı), Empty=░ (soluk)
    - Drone haritanın ALTINDAN dikey kalkıp hedefe gider, kısa hover yapar, yine aşağı iner.
      Arkada iz bırakmaz; küçük ASCII sprite olarak çizilir.
    """
    def enter(self):
        import random, pygame  # güvenlik: modüler import
        self.rows = QUARRY_ROWS
        self.cols = QUARRY_COLS

        # 0: empty, 1: limited, 2: rich
        self.grid = [[self._roll_cell() for _ in range(self.cols)] for _ in range(self.rows)]

        self.sel_r, self.sel_c = 0, 0
        self.extract_amt = 2

        # cooldown / anim
        self.cooldown  = 0.0
        self.anim_t    = 0.0
        self.anim_run  = False
        self.anim_src  = None   # (x,y) kaynağı
        self.anim_dst  = None   # (x,y) hedef hücre merkezi

        self.total_yield = 0
        self.last_msg    = "Use arrows to choose a cell; Enter to extract."

        # fonts
        self.font_big    = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 26, bold=True)
        self.font_label  = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 20, bold=True)
        self.font_body   = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 18)
        self.font_small  = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 16)
        self.font_ascii  = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 18, bold=True)

        self.row_labels = [chr(ord('A') + i) for i in range(self.rows)]
        self.col_labels = [str(j+1) for j in range(self.cols)]

        # --- drone ASCII sprite (küçük ve okunaklı; metin YOK, sadece şekil) ---
        self.drone_art = [
            "   __   ",
            " _/  \\_ ",
            " \\_==_/ ",
            "  /~~\\  ",
        ]
        self.drone_color = (120, 220, 220)  # CYAN
        self._flash_cell = None  # (r,c,color,remaining)

    def _roll_cell(self):
        import random
        r = random.random()
        if r < 0.18: return 2
        if r < 0.55: return 1
        return 0

    def _grid_rect_and_metrics(self, s):
        w, h = s.get_size()
        content = draw_header_with_right_logo(s, TITLE_TEXT, logo_scale_h=0.55, top_pad=36, side_pad=40)

        # Grid alanını %62'ye çek, sağ panele daha çok yer aç
        max_w = int(content.width * 0.62)
        max_h = int(content.height * 0.85)

        cell_w = max(16, min((max_w-60)//self.cols, (max_h-60)//self.rows))
        cell_h = cell_w

        grid_w = cell_w * self.cols + 40
        grid_h = cell_h * self.rows + 40

        gx = content.left
        gy = content.top + 8
        grid_rect = pygame.Rect(gx, gy, grid_w, grid_h)

        # Sağ panel — minimumu büyüttük (320→380)
        info_left = grid_rect.right + 24
        info_rect = pygame.Rect(info_left, gy, max(380, content.right - info_left), grid_h)

        return content, grid_rect, info_rect, cell_w, cell_h

    def _cell_center(self, grid_rect, cell_w, cell_h, r, c):
        x = grid_rect.left + 30 + c*cell_w + cell_w//2
        y = grid_rect.top  + 30 + r*cell_h + cell_h//2
        return x, y

    def handle(self, e):
        import pygame
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                from .menu import MenuScene
                self.app.scenes.switch(MenuScene); return

            if e.key == pygame.K_F11:
                self.app.toggle_fullscreen(); return

            # cooldown sırasında yalnızca ESC/F11 izinli
            if self.cooldown > 0.0:
                return

            if e.key in (pygame.K_UP, pygame.K_w):      self.sel_r = (self.sel_r - 1) % self.rows
            elif e.key in (pygame.K_DOWN, pygame.K_s):  self.sel_r = (self.sel_r + 1) % self.rows
            elif e.key in (pygame.K_LEFT, pygame.K_a):  self.sel_c = (self.sel_c - 1) % self.cols
            elif e.key in (pygame.K_RIGHT, pygame.K_d): self.sel_c = (self.sel_c + 1) % self.cols

            elif e.key == pygame.K_LEFTBRACKET:         self.extract_amt = max(1, self.extract_amt - 1)   # [
            elif e.key == pygame.K_RIGHTBRACKET:        self.extract_amt = min(9, self.extract_amt + 1)   # ]
            elif pygame.K_1 <= e.key <= pygame.K_9:     self.extract_amt = min(9, (e.key - pygame.K_0))

            elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._start_extraction()

    def _start_extraction(self):
    
        r, c = self.sel_r, self.sel_c
        richness = self.grid[r][c]

        # ÖNCE boş kontrolü: boşsa toplama YASAK
        if richness <= 0:
            self.last_msg = f"{self._coord_text(r,c)} is EMPTY — extraction blocked."
            # Kısa kırmızı flaş; cooldown/anim YOK
            self._flash_cell = (r, c, (220, 40, 40), 0.35)  # parlak kırmızı
            # Minik 'error' bip (opsiyonel)
            try:
                if pygame.mixer.get_init():
                    err = pygame.mixer.Sound(buffer=(b"\x00\x80"*600))
                    err.set_volume(0.25)
                    err.play()
            except Exception:
                pass
            return  # erken çıkış

        gained = 0
        flash_col = (225, 205, 80)  # default: limited için sarı (gerekirse override)

        if richness == 1:
            gained = min(1, self.extract_amt)
            self.grid[r][c] = 0
            flash_col = (225, 205, 80)  # YELLOW
            self.last_msg = f"Limited yield at {self._coord_text(r,c)}: +{gained}"
        else:  # richness == 2
            gained = min(2, self.extract_amt)
            self.grid[r][c] = max(0, 2 - gained)
            flash_col = (90, 220, 120)  # GREEN
            self.last_msg = f"Rich vein at {self._coord_text(r,c)}: +{gained}"

        self.total_yield += gained

        # cooldown / anim
        self.cooldown = float(QUARRY_COOLDOWN)
        self.anim_t   = 0.0
        self.anim_run = True

        s = self.app.screen
        _, grid_rect, _, cell_w, cell_h = self._grid_rect_and_metrics(s)

        # Hedef hücre merkezi:
        self.anim_dst = self._cell_center(grid_rect, cell_w, cell_h, r, c)

        # Kaynak: grid ALTINDAN (aynı sütuna hizalı), biraz aşağıdan başlasın
        start_y = grid_rect.bottom + max(20, cell_h)
        self.anim_src = (self.anim_dst[0], start_y)

        self._flash_cell = (r, c, flash_col, 0.28)

        # minik tık
        try:
            if pygame.mixer.get_init():
                click = pygame.mixer.Sound(buffer=(b"\x00\x00"*300))
                click.play()
        except Exception:
            pass

    def update(self, dt):
        # Hücre flaşı sönümü
        if self._flash_cell:
            r, c, col, t = self._flash_cell
            t -= dt
            self._flash_cell = (r, c, col, t) if t > 0 else None

        # Cooldown / anim
        if self.cooldown > 0.0:
            self.cooldown = max(0.0, self.cooldown - dt)
            if self.anim_run:
                # anim_t: 0→1 cooldown boyunca
                self.anim_t = min(1.0, self.anim_t + dt / max(0.0001, QUARRY_COOLDOWN))
                if self.anim_t >= 1.0:
                    self.anim_run = False

    def _coord_text(self, r, c):
        return f"{chr(ord('A')+r)}{c+1}"

    def _draw_grid(self, s, grid_rect, cell_w, cell_h):
        # panel arka planı
        panel = pygame.Surface(grid_rect.size, pygame.SRCALPHA)
        panel.fill((0, 30, 0, 120))
        s.blit(panel, grid_rect.topleft)
        pygame.draw.rect(s, BORDER, grid_rect, 1)

        # üst/sol etiketler
        for i, lab in enumerate(self.col_labels):
            draw_text(s, lab, 16, ACCENT,
                      topleft=(grid_rect.left + 30 + i*cell_w + cell_w//2 - 8, grid_rect.top + 6))
        for j, lab in enumerate(self.row_labels):
            draw_text(s, lab, 16, ACCENT,
                      topleft=(grid_rect.left + 6, grid_rect.top + 30 + j*cell_h + cell_h//2 - 10))

        # ASCII dokulu hücreler
        for r in range(self.rows):
            for c in range(self.cols):
                x = grid_rect.left + 30 + c*cell_w
                y = grid_rect.top  + 30 + r*cell_h
                rect = pygame.Rect(x, y, cell_w-2, cell_h-2)

                richness = self.grid[r][c]
                if richness >= 2:
                    col, ch = (90, 220, 120), "█"   # Rich → yeşil
                elif richness == 1:
                    col, ch = (225, 205, 80), "▓"  # Limited → sarı
                else:
                    # EMPTY → parlak kırmızı
                    col, ch = (220, 40, 40), "░"

                # flaş override
                if self._flash_cell:
                    fr, fc, fcol, _ = self._flash_cell
                    if fr == r and fc == c:
                        col = fcol

                # arka blok + çerçeve
                pygame.draw.rect(s, col, rect, border_radius=2)
                pygame.draw.rect(s, BORDER, rect, 1)

                # ortalı ASCII karakter
                glyph = self.font_ascii.render(ch, True, (0, 25, 0))
                gr = glyph.get_rect(center=(rect.centerx, rect.centery))
                s.blit(glyph, gr)

        # seçim çerçevesi (parlak)
        sel_x = grid_rect.left + 30 + self.sel_c*cell_w
        sel_y = grid_rect.top  + 30 + self.sel_r*cell_h
        sel_r = pygame.Rect(sel_x, sel_y, cell_w-2, cell_h-2)
        pygame.draw.rect(s, (120, 220, 220), sel_r, 2)  # CYAN

    def _draw_info_panel(self, s, info_rect):
        panel = pygame.Surface(info_rect.size, pygame.SRCALPHA)
        panel.fill((0, 30, 0, 120))
        s.blit(panel, info_rect.topleft)
        pygame.draw.rect(s, BORDER, info_rect, 1)

        tx, ty = info_rect.left + 12, info_rect.top + 10
        draw_text(s, "Black Rock Quarry", 20, FG, topleft=(tx, ty)); ty += 26

        draw_text(s, f"Selected: {self._coord_text(self.sel_r, self.sel_c)}", 18, ACCENT, topleft=(tx, ty)); ty += 22
        draw_text(s, f"Extraction amount: {self.extract_amt}", 18, ACCENT, topleft=(tx, ty)); ty += 22

        if self.cooldown > 0.0:
            draw_text(s, f"Cooldown: {self.cooldown:0.1f}s", 18, (225,205,80), topleft=(tx, ty)); ty += 22  # YELLOW
        else:
            draw_text(s, "Ready.", 18, (90,220,120), topleft=(tx, ty)); ty += 22  # GREEN

        ty += 6
        draw_text(s, f"Total Yield: {self.total_yield}", 18, FG, topleft=(tx, ty)); ty += 24
        pygame.draw.line(s, BORDER, (tx, ty), (info_rect.right-12, ty), 1); ty += 10

        guide = [
            "How it works:",
            "• Move with arrows / WASD.",
            "• Amount: [ / ] or 1–9.",
            "• Enter/Space to extract.",
            "• Drone ascends from below, hovers,",
            "  then returns during cooldown.",
            "• Cell richness: █ rich, ▓ limited, ░ empty.",
        ]
        for g in guide:
            draw_text(s, g, 16, MUTED, topleft=(tx, ty)); ty += 20

        ty = info_rect.bottom - 68
        draw_text(s, "Enter: extract  •  ESC: back  •  F11: fullscreen", 16, MUTED, topleft=(tx, ty))

    def _draw_drone(self, s, grid_rect):
        import math, pygame
        if not self.anim_run and self.cooldown <= 0.0:
            return
        if not self.anim_src or not self.anim_dst:
            return

        # Fazlar:
        # 0.00–0.45: dikey çıkış (src.y -> dst.y)
        # 0.45–0.55: hover (ufak bob)
        # 0.55–1.00: dikey iniş (dst.y -> src.y)
        t = max(0.0, min(1.0, self.anim_t))

        def ease_in_out(x):
            # smootherstep benzeri
            return x*x*(3 - 2*x)

        x = self.anim_dst[0]            # X sabit; hep hedef sütuna hizalı
        src_y = self.anim_src[1]
        dst_y = self.anim_dst[1]

        if t < 0.45:
            # kalkış
            k = ease_in_out(t / 0.45)
            y = src_y + (dst_y - src_y) * k
        elif t < 0.55:
            # hover (yumuşak bob)
            y = dst_y + math.sin(pygame.time.get_ticks() * 0.012) * 2.0
        else:
            # iniş
            k = ease_in_out((t - 0.55) / 0.45)
            y = dst_y + (src_y - dst_y) * k

        # ASCII sprite'ı merkezleyerek çiz (gölge + ana)
        offx = -len(self.drone_art[0]) * 6 // 2   # ~6 px/char tahmini
        offy = -len(self.drone_art) * 7 // 2

        for i, line in enumerate(self.drone_art):
            shadow = self.font_body.render(line, True, (0, 0, 0))
            s.blit(shadow, (int(x) + offx + 1, int(y) + offy + i * 14 + 1))

        for i, line in enumerate(self.drone_art):
            glyph = self.font_body.render(line, True, self.drone_color)
            s.blit(glyph, (int(x) + offx, int(y) + offy + i * 14))

    def draw(self, s):
        s.fill(BG)
        content, grid_rect, info_rect, cell_w, cell_h = self._grid_rect_and_metrics(s)

        draw_text(s, "Quarry: ↑↓←→ move • [ / ] amount • 1–9 set • Enter extract • ESC back",
                  18, MUTED, topleft=(content.left, content.top - 20))

        self._draw_grid(s, grid_rect, cell_w, cell_h)
        self._draw_info_panel(s, info_rect)
        self._draw_drone(s, grid_rect)

        draw_text(s, self.last_msg, 18, MUTED, topleft=(content.left, content.bottom + 8))

# -*- coding: utf-8 -*-
import os, pygame

from ..settings import (
    BG, FG, ACCENT, MUTED, BORDER,
    TITLE_TEXT, LOGO_PATH, AUDIOS_DIR
)
from ..core.scene import Scene
from ..utils.gfx import draw_text, draw_header_with_right_logo
from ..utils.audio import transcode_to_temp_wav  # utils/audio.py

# ---------- Helpers ----------
def _list_audio_pairs():
    """
    audios/ klasöründe aynı ada sahip .mp3 (veya .MP3) ile .txt (veya .TXT) dosyalarını eşler.
    return: [(base_name, mp3_path, txt_path), ...] (alfabetik)
    """
    if not os.path.isdir(AUDIOS_DIR):
        return []

    mp3s = {}
    for n in os.listdir(AUDIOS_DIR):
        if n.lower().endswith(".mp3"):
            base = os.path.splitext(n)[0]
            mp3s[base] = os.path.join(AUDIOS_DIR, n)

    pairs = []
    for n in os.listdir(AUDIOS_DIR):
        if n.lower().endswith(".txt"):
            base = os.path.splitext(n)[0]
            if base in mp3s:
                pairs.append((base, mp3s[base], os.path.join(AUDIOS_DIR, n)))
    pairs.sort(key=lambda x: x[0].lower())
    return pairs


# ---------- List ----------
class AudioLogsList(Scene):
    def enter(self):
        self.items = _list_audio_pairs()
        self.sel = 0
        self.line_h = pygame.font.SysFont("consolas,monospace", 24).get_height() + 6

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                from .menu import MenuScene
                self.app.scenes.switch(MenuScene)
            elif self.items:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = max(0, self.sel - 1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = min(len(self.items) - 1, self.sel + 1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    base, mp3, txt = self.items[self.sel]
                    self.app.scenes.switch(lambda app: AudioLogScene(app, base, mp3, txt))
                elif e.key == pygame.K_F11:
                    self.app.toggle_fullscreen()

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.52, top_pad=36, side_pad=40
        )
        draw_text(s, "Audio Logs", 22, FG, topleft=(content.left, content.top - 8))
        draw_text(s, "Enter: open • SPACE: play/pause • ←/→: seek • ESC: back",
                  18, MUTED, topleft=(content.left, content.top + 20))

        if not self.items:
            draw_text(s, f'Place matching pairs (mp3 + txt) in "{AUDIOS_DIR}"', 22, ACCENT,
                      topleft=(content.left, content.top + 60))
            return

        import math
        t = pygame.time.get_ticks() / 1000.0
        pulse = 60 + int(60 * (0.5 + 0.5 * math.sin(t * 6)))

        y = content.top + 48
        area_h = content.bottom - y
        max_lines = max(1, area_h // self.line_h)
        start = max(0, self.sel - max_lines // 2)
        end   = min(len(self.items), start + max_lines)

        for i in range(start, end):
            base = self.items[i][0]
            label = f"{base}"
            if i == self.sel:
                rect = pygame.Rect(content.left - 8, y - 2, content.width + 8, self.line_h)
                pygame.draw.rect(s, (0, 255, 0, 70), rect, 0)  # hafif highlight
                draw_text(s, "▸", 24, FG, topleft=(content.left - 4, y))
                color = FG
            else:
                color = ACCENT
            draw_text(s, label, 24, color, topleft=(content.left + 18, y))
            y += self.line_h


# ---------- AudioPlayer ----------
class AudioLogScene(Scene):
    """
    Sol: transcript (wrap + scroll, küçük font)
    Sağ: kontroller/meta
    MP3 direkt yüklenemezse ffmpeg ile temp WAV'a çevrilir.
    """
    def __init__(self, app, base_name, mp3_path, txt_path):
        super().__init__(app)
        self.base_name = base_name
        self.mp3_path  = mp3_path
        self.txt_path  = txt_path

        # UI
        self.scroll_y   = 0
        self.scroll_v   = 28
        self.line_gap   = 4
        self.par_gap    = 8

        # fonts
        self.font_body  = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 18)
        self.font_small = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 14)

        # content
        self.transcript_text = "Loading transcript…"
        self._audio_loaded = False
        self._tmp_audio = None  # temp WAV

    def enter(self):
        # transcript
        try:
            with open(self.txt_path, "r", encoding="utf-8", errors="replace") as f:
                self.transcript_text = f.read().strip() or "(empty transcript)"
        except Exception as e:
            self.transcript_text = f"Transcript not found.\n{self.txt_path}\n{e}"
            self.app.push_info("Transcript could not be loaded.")

        # audio
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 1024)
                pygame.mixer.init()
        except Exception:
            pass

        # 1) TRY MP3
        try:
            pygame.mixer.music.load(self.mp3_path)
            self._audio_loaded = True
        except Exception:
            # 2) ffmpeg -> temp wav
            wav_path = transcode_to_temp_wav(self.mp3_path)
            if wav_path:
                try:
                    pygame.mixer.music.load(wav_path)
                    self._tmp_audio = wav_path
                    self._audio_loaded = True
                except Exception:
                    self._audio_loaded = False
            else:
                self._audio_loaded = False

        if not self._audio_loaded:
            self.app.push_info("Audio could not be loaded (try installing ffmpeg).")
        else:
            try:
                pygame.mixer.music.set_volume(0.9)
                pygame.mixer.music.play()
            except Exception:
                pass

    def cleanup(self):
        # temp wav delete
        if self._tmp_audio and os.path.exists(self._tmp_audio):
            try: os.remove(self._tmp_audio)
            except Exception: pass
            self._tmp_audio = None

    def exit(self):
        self.cleanup()

    # --- wrap + scroll ---
    def _draw_text_wrapped(self, surface, rect, text, font, color, line_gap=4, par_gap=8):
        x, y, w, h = rect
        max_y = y + h
        cur_y = y
        paragraphs = [p.strip() for p in text.replace("\r\n","\n").split("\n\n")]

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

    # --- input ---
    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                try: pygame.mixer.music.stop()
                except Exception: pass
                from .audios import AudioLogsList
                self.app.scenes.switch(AudioLogsList)

            # scroll
            elif e.key in (pygame.K_PAGEUP,):
                self.scroll_y = max(0, self.scroll_y - self.scroll_v * 4)
            elif e.key in (pygame.K_PAGEDOWN,):
                self.scroll_y += self.scroll_v * 4
            elif e.key == pygame.K_UP:
                self.scroll_y = max(0, self.scroll_y - self.scroll_v)
            elif e.key == pygame.K_DOWN:
                self.scroll_y += self.scroll_v

            # audio controls
            elif e.key == pygame.K_SPACE and self._audio_loaded:
                try:
                    if pygame.mixer.music.get_busy():
                        pygame.mixer.music.pause()
                    else:
                        pygame.mixer.music.unpause()
                except Exception:
                    pass
            elif e.key == pygame.K_s and self._audio_loaded:
                try: pygame.mixer.music.stop()
                except Exception: pass
            elif e.key == pygame.K_r and self._audio_loaded:
                try:
                    pygame.mixer.music.stop()
                    pygame.mixer.music.play()
                except Exception:
                    pass
            elif e.key == pygame.K_LEFT and self._audio_loaded:
                try:
                    pos = max(0.0, pygame.mixer.music.get_pos()/1000.0 - 5.0)
                    pygame.mixer.music.play(start=pos)
                except Exception:
                    pass
            elif e.key == pygame.K_RIGHT and self._audio_loaded:
                try:
                    pos = max(0.0, pygame.mixer.music.get_pos()/1000.0 + 5.0)
                    pygame.mixer.music.play(start=pos)
                except Exception:
                    pass

        elif e.type == pygame.MOUSEWHEEL:
            self.scroll_y = max(0, self.scroll_y - e.y*self.scroll_v)

    def update(self, dt): pass

    def draw(self, s):
        s.fill(BG)
       
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )

        full = s.get_rect()
        margin = 16

        
        left_w  = int(content.width * 0.62)
        right_w = int(content.width * 0.36)

        left_rect  = pygame.Rect(content.left - 10, content.top + 8, left_w, int(full.height * 0.70))
        right_rect = pygame.Rect(content.right - right_w, content.top + 8, right_w, int(full.height * 0.70))

        # WARNING
        bottom_guard = full.height - 200
        left_rect.height  = min(left_rect.height,  bottom_guard - left_rect.top - margin)
        right_rect.height = min(right_rect.height, bottom_guard - right_rect.top - margin)

        # Transcript
        panelL = pygame.Surface((left_rect.width, left_rect.height), pygame.SRCALPHA)
        panelL.fill((0, 30, 0, 120))
        pygame.draw.rect(panelL, BORDER, panelL.get_rect(), 1)

        inner_pad = 10
        text_rect = pygame.Rect(inner_pad, inner_pad,
                                left_rect.width - inner_pad*2,
                                left_rect.height - inner_pad*2)

        # viewport
        view = pygame.Surface((text_rect.width, text_rect.height), pygame.SRCALPHA)
        big_h = max(text_rect.height * 3, 5000)
        canvas = pygame.Surface((text_rect.width, big_h), pygame.SRCALPHA)

        used_h = self._draw_text_wrapped(
            canvas, (0, 0, text_rect.width, big_h),
            self.transcript_text, self.font_body, FG,
            line_gap=self.line_gap, par_gap=self.par_gap
        )
        max_scroll = max(0, used_h - text_rect.height)
        if self.scroll_y > max_scroll:
            self.scroll_y = max_scroll

        src_rect = pygame.Rect(0, self.scroll_y, text_rect.width, text_rect.height)
        view.blit(canvas, (0, 0), src_rect)
        panelL.blit(view, (text_rect.left, text_rect.top))
        s.blit(panelL, left_rect.topleft)
        draw_text(s, "Audio Log — Transcript", 18, ACCENT, topleft=(left_rect.left, left_rect.top - 22))

        # Kontroller/Meta
        panelR = pygame.Surface((right_rect.width, right_rect.height), pygame.SRCALPHA)
        panelR.fill((0, 30, 0, 120))
        pygame.draw.rect(panelR, BORDER, panelR.get_rect(), 1)

        tx = 12; ty = 12
        panelR.blit(self.font_small.render("Controls", True, FG), (tx, ty)); ty += 22
        panelR.blit(self.font_small.render("SPACE: play/pause", True, MUTED), (tx, ty)); ty += 18
        panelR.blit(self.font_small.render("S: stop  •  R: restart", True, MUTED), (tx, ty)); ty += 18
        panelR.blit(self.font_small.render("←/→: seek ±5s", True, MUTED), (tx, ty)); ty += 18

        pygame.draw.line(panelR, BORDER, (10, ty+8), (right_rect.width-10, ty+8), 1)
        ty += 16
        panelR.blit(self.font_small.render("Meta", True, FG), (tx, ty)); ty += 20

        try:
            nm = os.path.basename(self.mp3_path)
            panelR.blit(self.font_small.render(f"File: {nm}", True, MUTED), (tx, ty)); ty += 18
            from datetime import datetime
            mtime = datetime.fromtimestamp(os.path.getmtime(self.mp3_path)).strftime("%Y-%m-%d %H:%M")
            panelR.blit(self.font_small.render(f"Modified: {mtime}", True, MUTED), (tx, ty)); ty += 18
        except Exception:
            pass

        s.blit(panelR, right_rect.topleft)

        draw_text(
            s,
            "Scroll: MouseWheel / PgUp/PgDn / ↑↓   •   ESC: back",
            18, MUTED,
            topleft=(content.left, max(left_rect.bottom, right_rect.bottom) + 8)
        )

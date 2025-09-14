# -*- coding: utf-8 -*-
import os, random, math, pygame
from ..settings import FG, ACCENT, MUTED, BORDER, BG, AHTI_IMAGE, AHTI_SONG, AHTI_CHANNEL_ID
from ..utils.audio import transcode_to_temp_wav

class AhtiOverlay:
    """
    J ile aç/kapat. Solda Ahti.png küçük, sağda 3-4 alıntı. Arka planda Sankarin Tango loop.
    Kapanınca müzik durur, varsa önceki pygame.mixer.music unpause edilmez (global music’i etkilemeyiz).
    """
    def __init__(self, app):
        self.app = app
        self._t = 0.0
        self._opening = True
        self._closing = False
        self._blink_t = 0.0

        w, h = self.app.screen.get_size()
        self.font_big   = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 28, bold=True)
        self.font_body  = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 20)
        self.font_small = pygame.font.SysFont("consolas,menlo,dejavusansmono,monospace", 16)

        # image
        self.photo = None
        try:
            img = pygame.image.load(AHTI_IMAGE).convert_alpha()
            max_h = int(h * 0.30)
            scale = min(1.0, max_h / img.get_height())
            self.photo = pygame.transform.smoothscale(img, (int(img.get_width()*scale), int(img.get_height()*scale)))
        except Exception:
            pass

        # quotes (dilersen AhtiQuotes.txt ile override)
        self.quotes = [
            "You'll take care of it; this crisis will be last winter's snow.",
            "This song is a present from my friends to you.",
            "Better than somebody with no face at all.",
            "Earth is a cyclical song."
        ]
        try:
            if os.path.exists("AhtiQuotes.txt"):
                with open("AhtiQuotes.txt","r",encoding="utf-8") as f:
                    qs = [ln.strip() for ln in f if ln.strip()]
                    if qs: self.quotes = qs
        except Exception:
            pass
        random.shuffle(self.quotes)
        self._show_n = min(4, len(self.quotes))

        # music on dedicated channel
        self._chan = None
        self._snd  = None
        self._tmp  = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 1024)
                pygame.mixer.init()
            try:
                self._snd = pygame.mixer.Sound(AHTI_SONG)
            except Exception:
                wav = transcode_to_temp_wav(AHTI_SONG)
                if wav: self._tmp = wav; self._snd = pygame.mixer.Sound(wav)
            if self._snd:
                self._chan = pygame.mixer.Channel(AHTI_CHANNEL_ID)
                self._chan.set_volume(0.55)
                self._chan.play(self._snd, loops=-1)
        except Exception:
            pass

        self._layout = self._compute_layout(w, h)

    def _compute_layout(self, w, h):
        left_x, top_y = 40, 90
        photo_w = self.photo.get_width() if self.photo else 240
        panel_w = int(w * 0.52)
        panel_h = int(h * 0.60)
        panel_x = min(w - panel_w - 40, left_x + photo_w + 40)
        panel_y = top_y
        return {"left_x": left_x, "top_y": top_y, "panel": (panel_x, panel_y, panel_w, panel_h)}

    def _ease_out(self, x): return 1 - (1 - x) ** 3

    def update(self, dt):
        self._blink_t += dt
        if self._opening and not self._closing:
            self._t = min(1.0, self._t + dt * 2.2)
            if self._t >= 1.0: self._opening = False
        elif self._closing:
            self._t = max(0.0, self._t - dt * 2.2)
            if self._t <= 0.0: self._finish_close()

    def draw(self, s):
        w, h = s.get_size()
        left_x = self._layout["left_x"]; top_y = self._layout["top_y"]
        px, py, pw, ph = self._layout["panel"]

        # veil
        alpha = int(180 * self._ease_out(self._t))
        veil = pygame.Surface((w,h), pygame.SRCALPHA); veil.fill((10, 8, 0, alpha))
        s.blit(veil, (0,0))

        # title
        head = self.font_big.render("Ahti speaks…", True, (230,230,210))
        head.set_alpha(int(255*self._t))
        s.blit(head, (24,24))

        # photo
        if self.photo:
            dy = int((1.0 - self._ease_out(self._t)) * 20)
            img = self.photo.copy(); img.set_alpha(int(255*self._t))
            s.blit(img, (left_x, top_y - dy))
            r = img.get_rect(topleft=(left_x, top_y - dy))
            pygame.draw.rect(s, BORDER, r, 1)

        # panel
        start_x = w + 40
        cur_x = int(start_x + (px - start_x) * self._ease_out(self._t))
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((0, 30, 0, int(140*self._t)))
        pygame.draw.rect(panel, BORDER, panel.get_rect(), 1)

        tx, ty = 16, 14
        tip = self.font_small.render("Press J to dismiss", True, (160,180,160))
        tip.set_alpha(int(255*self._t)); panel.blit(tip, (tx, ty)); ty += 28

        for i in range(self._show_n):
            q = self.quotes[i]
            bullet = "» "
            max_w = pw - tx*2 - self.font_body.size(bullet)[0]
            # wrap
            words = q.split(); line = ""
            for wtok in words:
                test = (line + " " + wtok).strip()
                if self.font_body.size(test)[0] <= max_w:
                    line = test
                else:
                    panel.blit(self.font_body.render(bullet+line, True, FG), (tx, ty))
                    ty += self.font_body.get_height() + 6
                    line = wtok
            if line:
                panel.blit(self.font_body.render(bullet+line, True, FG), (tx, ty))
                ty += self.font_body.get_height() + 14

        src = self.font_small.render("Quotes: Control / Alan Wake II", True, (140,160,140))
        src.set_alpha(int(255*self._t))
        panel.blit(src, (tx, ph - 26))
        s.blit(panel, (cur_x, py))

        if int(self._blink_t*2)%2==0 and self._t>0.2:
            dot = self.font_small.render("●", True, (200,60,60))
            s.blit(dot, (w-28, 26))

    def close(self): self._closing = True

    def _finish_close(self):
        try:
            if self._chan: self._chan.stop()
        except Exception: pass
        try:
            if self._tmp and os.path.exists(self._tmp): os.remove(self._tmp)
        except Exception: pass
        self._tmp = None
    def _stop_song(self, fade_ms=0):
        try:
            if self._chan:
                self._chan.stop()
        except Exception: pass
        try:
            if self._tmp and os.path.exists(self._tmp):
                os.remove(self._tmp)
        except Exception: pass
        self._tmp = None

    def close(self):
        # müziği hemen kes
        self._stop_song(0)
        # varsa arka plan müziğini geri getir
        try:
            if self._had_music:
                pygame.mixer.music.unpause()
        except Exception: pass
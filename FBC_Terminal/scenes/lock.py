import pygame
from ..settings import (
    BG, FG, ACCENT, MUTED, BORDER, TITLE_TEXT, LOGO_PATH,
    LOCK_CODE, LOCK_PASS2, LOCK_ATTEMPTS, LOCK_HINT
)
from ..utils.gfx import draw_text, draw_header_with_right_logo
from ..utils.audio import make_beep_sequence
from ..overlays.decrypt import DecryptOverlay
from .menu import MenuScene

class LockPrompt:
    """
    Basit erişim doğrulama: CODE ya da PASS-PHRASE gir. ENTER ile onay.
    F1 ipucu. 3 kere yanlışta “ACCESS DENIED” ve timer ile uygulama kapanır.
    """
    def __init__(self, app):
        self.app = app

    def enter(self):
        self.input_buf = ""
        self.message = "SECURITY CHECK // ENTER ACCESS CODE"
        self.attempts_left = LOCK_ATTEMPTS
        self.cursor_on = True
        self.cursor_t = 0.0
        self.shake_t = 0.0
        self.denied = False
        # sesler
        self.snd_ok  = make_beep_sequence(count=2, freq=880, beep_ms=90, pause_ms=90)
        self.snd_err = make_beep_sequence(count=2, freq=320, beep_ms=50, pause_ms=70, volume=0.22)

    def exit(self):
        pass

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                self.app.running = False
                return
            if self.denied:
                return
            if e.key == pygame.K_RETURN:
                self._try_unlock()
                return
            if e.key == pygame.K_BACKSPACE:
                self.input_buf = self.input_buf[:-1]
                return
            if e.key == pygame.K_F1:
                self.message = LOCK_HINT
                return
            
            ch = e.unicode
            if ch and (ch.isalnum() or ch in " -_"):
                if len(self.input_buf) < 32:
                    self.input_buf += ch.upper()

        elif e.type == pygame.USEREVENT+42:
            # ACCESS DENIED
            self.app.running = False

    def update(self, dt):
        self.cursor_t += dt
        if self.cursor_t > 0.5:
            self.cursor_t = 0.0
            self.cursor_on = not self.cursor_on
        if self.shake_t > 0:
            self.shake_t = max(0.0, self.shake_t - dt)

    def draw(self, s):
        s.fill(BG)
        w, h = s.get_size()

        content = draw_header_with_right_logo(
            s, f"{TITLE_TEXT} - Terminal", logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )

        # Panel
        card_w, card_h = min(720, int(w*0.82)), 220
        cx, cy = w//2, int(h*0.52)
        card = pygame.Rect(0, 0, card_w, card_h); card.center = (cx, cy)

        ox = int(6 * (self.shake_t > 0) * (1 if (pygame.time.get_ticks()//40)%2==0 else -1))

        panel = pygame.Surface((card.width, card.height), pygame.SRCALPHA)
        panel.fill((0, 25, 0, 160))
        s.blit(panel, (card.left+ox, card.top))
        pygame.draw.rect(s, BORDER, card.move(ox, 0), 1)

        draw_text(s, self.message, 22, ACCENT, center=(cx+ox, card.top+28))
        draw_text(s, "CODE or PASS-PHRASE:", 18, MUTED, topleft=(card.left+24+ox, card.top+64))

        caret = "▎" if self.cursor_on else " "
        draw_text(s, f"> {self.input_buf}{caret}", 28, FG, topleft=(card.left+24+ox, card.top+94))

        draw_text(s, "F1: hint  •  ENTER: submit  •  ESC: quit", 18, MUTED, center=(cx+ox, card.bottom-18))

    # --- helpers ---
    def _try_unlock(self):
        txt = self.input_buf.strip().upper()
        if txt == LOCK_CODE or txt == LOCK_PASS2.upper():
            try: self.snd_ok.play()
            except: pass
            self.app.push_info("ACCESS GRANTED")
            self.app.active_overlay = DecryptOverlay(self.app, duration=1.8, on_done=lambda: self.app.scenes.switch(MenuScene))
            self.app.scenes.switch(MenuScene)
        else:
            self.attempts_left -= 1
            self.input_buf = ""
            self.shake_t = 0.35
            try: self.snd_err.play()
            except: pass
            if self.attempts_left <= 0:
                self.denied = True
                self.message = "ACCESS DENIED"
                pygame.time.set_timer(pygame.USEREVENT+42, 1200, loops=1)
            else:
                self.message = f"INVALID. Attempts left: {self.attempts_left}"

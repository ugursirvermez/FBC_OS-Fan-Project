import pygame
from ..settings import BG, MUTED, FG, TITLE_TEXT, LOGO_PATH, SPLASH_DURATION, LOCK_ENABLED
from ..utils.gfx import draw_text, draw_header_with_right_logo

class SplashScene:
    """Minimal splash: logo+header. ESC/Enter/Space to Exit."""
    def __init__(self, app):
        self.app = app
        self.t = 0.0

    def enter(self):
        self.t = 0.0

    def exit(self):
        pass

    def handle(self, e):
        if e.type == pygame.KEYDOWN and e.key in (pygame.K_ESCAPE, pygame.K_RETURN, pygame.K_SPACE):
            self._finish()

    def update(self, dt):
        self.t += dt
        if self.t >= SPLASH_DURATION:
            self._finish()

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, f"{TITLE_TEXT} - Terminal", logo_path=LOGO_PATH, logo_scale_h=0.55, top_pad=36, side_pad=40
        )
        draw_text(s, "Press ESC to skip", 18, MUTED, topleft=(content.left, content.top - 20))
        draw_text(s, "Initializing subsystems…", 20, FG, center=(s.get_width()//2, s.get_height()//2 + 40))

    # --- helpers ---
    def _finish(self):
        # Lock kapalıysa direkt menüye
        if not LOCK_ENABLED:
            from .menu import MenuScene
            self.app.scenes.switch(MenuScene)
        else:
            from .lock import LockPrompt
            self.app.scenes.switch(LockPrompt)

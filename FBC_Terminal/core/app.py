#Libraries
#Terminal Working Right Here!
import pygame,random,sys,subprocess,os
from ..settings import *
from .scene import SceneManager
from ..utils.gfx import make_scanlines, draw_text
from ..overlays.ahti import AhtiOverlay
from ..overlays.decrypt import DecryptOverlay
from ..overlays.threshold import ThresholdOverlay
from ..settings import THRESHOLD_MIN_DELAY, THRESHOLD_MAX_DELAY
from ..scenes.splash import SplashScene
from ..utils.audio import *

class App:
    def __init__(self):
        pygame.init(); pygame.font.init()
        flags = pygame.FULLSCREEN if FULLSCREEN else pygame.RESIZABLE
        self.screen = pygame.display.set_mode((0, 0), flags)
        pygame.display.set_caption("Bureau OS — Pygame (FBC Terminal)")
        if os.path.exists(icon_path):
            try:
                pygame.display.set_icon(pygame.image.load(icon_path))
            except Exception as e:
                print(f"Icon load failed: {e}")

        self.clock = pygame.time.Clock()

        self.running = True
        self.active_overlay = None
        self.scenes = SceneManager(self)

        self.scanlines = make_scanlines(self.screen.get_size(), alpha=36)
        self.info = None
        self.info_timer = 0.0
        
        self._next_threshold = random.uniform(THRESHOLD_MIN_DELAY, THRESHOLD_MAX_DELAY)
        
        # --- First Scene: Splash ---
        self.scenes.switch(SplashScene)
        self.init_sfx()

    def init_sfx(self):
        # Robust mixer init
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
            try:
                pygame.mixer.set_num_channels(16)
            except Exception:
                pass
        except Exception:
            return  

        self._last_keyclick_ms = 0
        self.key_sound = None

        try:
            if os.path.exists(KEYSOUND_FILE):
                self.key_sound = pygame.mixer.Sound(KEYSOUND_FILE)
                self.key_sound.set_volume(0.45)
            else:
                # print(f"[info] {KEYSOUND_FILE} not found — key click disabled.")
                self.key_sound = None
        except Exception:
            self.key_sound = None


    def play_key_click(self):
        """Global key click"""
        if not self.key_sound:
            return
        # Debounce: 30–40 ms
        now = pygame.time.get_ticks()
        if now - getattr(self, "_last_keyclick_ms", 0) < 35:
            return
        self._last_keyclick_ms = now

        try:
            # Mixer if closed
            if not pygame.mixer.get_init():
                self.init_sfx()
            ch = pygame.mixer.find_channel(True)  # force=True
            ch.play(self.key_sound)
        except Exception:
            pass


    def beep_ok(self): 
        try: make_beep_sequence(count=1, freq=980, beep_ms=100, volume=0.22).play()
        except Exception: pass

    def beep_err(self):
        try: make_beep_sequence(count=2, freq=320, beep_ms=50, pause_ms=70, volume=0.22).play()
        except Exception: pass

    def push_info(self, msg, seconds=2.5):
        self.info = msg
        self.info_timer = seconds

    def toggle_fullscreen(self):
        is_fs = self.screen.get_flags() & pygame.FULLSCREEN
        pygame.display.quit(); pygame.display.init()
        flags = 0 if is_fs else pygame.FULLSCREEN
        self.screen = pygame.display.set_mode((0, 0), flags)
        self.scanlines = make_scanlines(self.screen.get_size(), alpha=36)
        self.init_sfx()

    def run_oceanview(self):
        py = sys.executable
        game_path = os.path.join(ROOT_DIR, "FBC_Terminal/scenes/ocean_game.py")
        if not os.path.exists(game_path):
            self.push_info("ocean_game.py not found."); return

        try:
            ret = subprocess.call([py, game_path])
            
        except Exception as e:
            self.push_info(f"Oceanview failed: {e}")

        pygame.display.set_mode(self.screen.get_size(),
                                pygame.FULLSCREEN if (self.screen.get_flags() & pygame.FULLSCREEN) else 0)
        pygame.display.flip()
        
        self.push_info("Returned from Oceanview Motel")

    def run(self):
        while self.running:
            dt = self.clock.tick(self.fps)/1000.0 if hasattr(self, "fps") else self.clock.tick(60)/1000.0
            # Overlay
            if self.active_overlay:
                self.active_overlay.update(dt)
            else:
                self.scenes.scene.update(dt)

            # Threshold
                #if self._next_threshold is not None:
                #    self._next_threshold -= dt
                #if self._next_threshold <= 0:
                #    self.active_overlay = ThresholdOverlay(self)
                #    self._next_threshold = random.uniform(THRESHOLD_MIN_DELAY, THRESHOLD_MAX_DELAY)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                    continue

                if ev.type == pygame.KEYDOWN:
                    self.play_key_click()

                # --- Ahti Overlay toggle (J) ---
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_j:
                    if self.active_overlay and isinstance(self.active_overlay, AhtiOverlay):
                        try: self.active_overlay.close()
                        except Exception: pass
                        self.active_overlay = None
                    else:
                        self.active_overlay = AhtiOverlay(self)
                    continue  # sahneye paslamadan geç

                self.scenes.scene.handle(ev)
            # Draw
            self.scenes.scene.draw(self.screen)

            # Info bar
            if self.info_timer > 0 and self.info:
                self.info_timer -= dt
                r = pygame.Surface((self.screen.get_width(), 26), pygame.SRCALPHA)
                r.fill((0, 0, 0, 140))
                self.screen.blit(r, (0, 0))
                draw_text(self.screen, self.info, 18, FG, center=(self.screen.get_width() // 2, 13))
                if self.info_timer <= 0:
                    self.info = None

            # Overlay draw
            if self.active_overlay:
                self.active_overlay.draw(self.screen)

            self.screen.blit(self.scanlines, (0, 0))
            pygame.display.flip()

        pygame.quit()

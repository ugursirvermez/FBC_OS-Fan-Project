# scenes/hotline.py
import os, math, random, pygame
from ..utils.gfx import draw_text, make_scanlines
from ..utils.audio import make_beep_sequence, transcode_to_temp_wav
from ..settings import BG, FG, ACCENT, MUTED, ROOT_DIR

ASSET_DIR = os.path.join(ROOT_DIR, "assets", "hotline")
PHONE_PNG = os.path.join(ASSET_DIR, "hotline_phone.png")    
RING_WAV  = os.path.join(ASSET_DIR, "hotline_ring.mp3")      
MSG_MP3   = os.path.join(ASSET_DIR, "hotline_message.mp3")   

class HotlineScene:
    """Hotline Phone Room: play -> reply with E -> play text message -> ESC menu."""
    def __init__(self, app):
        self.app = app
        self.w, self.h = self.app.screen.get_size()
        self.room = pygame.Surface((self.w, self.h)).convert_alpha()
        self.scan = make_scanlines((self.w, self.h), alpha=36)

        self.t = 0.0
        self.wobble = True
        self.glitch_phase = 0.0
        self.answered = False
        self.playing_msg = False
        self.msg_tmp = None 

        self.phone_img = None
        if os.path.exists(PHONE_PNG):
            try:
                img = pygame.image.load(PHONE_PNG).convert_alpha()
                scale = min(1.0, (self.h * 0.85) / img.get_height())
                self.phone_img = pygame.transform.smoothscale(
                    img, (int(img.get_width()*scale), int(img.get_height()*scale))
                )
            except Exception:
                self.phone_img = None

        self.ring_snd = None
        self.msg_loaded = False
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 1024)
                pygame.mixer.init()
        except Exception:
            pass

        try:
            if os.path.exists(RING_WAV):
                self.ring_snd = pygame.mixer.Sound(RING_WAV)
                self.ring_snd.set_volume(0.35)
        except Exception:
            self.ring_snd = None

        try:
            if os.path.exists(MSG_MP3):
                try:
                    pygame.mixer.music.load(MSG_MP3)
                    self.msg_loaded = True
                except Exception:
                    tmp = transcode_to_temp_wav(MSG_MP3)
                    if tmp:
                        pygame.mixer.music.load(tmp)
                        self.msg_tmp = tmp
                        self.msg_loaded = True
        except Exception:
            self.msg_loaded = False

        self._start_ringing()

    # ————— lifecycle —————
    def enter(self): pass
    def exit(self):
        self._stop_all_audio()
        if self.msg_tmp and os.path.exists(self.msg_tmp):
            try: os.remove(self.msg_tmp)
            except Exception: pass

    # ————— audio helpers —————
    def _start_ringing(self):
        
        if self.ring_snd:
            try: self.ring_snd.play(loops=-1)
            except Exception: pass
        else:
            try: make_beep_sequence(count=2, beep_ms=120, pause_ms=200, freq=620, volume=0.22).play()
            except Exception: pass

    def _stop_ringing(self):
        try:
            if self.ring_snd:
                self.ring_snd.stop()
        except Exception:
            pass

    def _play_message(self):
        if not self.msg_loaded:
            
            try: make_beep_sequence(count=1, beep_ms=180, pause_ms=0, freq=520, volume=0.22).play()
            except Exception: pass
            self.playing_msg = True
            return
        try:
            pygame.mixer.music.set_volume(0.90)
            pygame.mixer.music.play()
            self.playing_msg = True
        except Exception:
            self.playing_msg = False

    def _stop_all_audio(self):
        self._stop_ringing()
        try: pygame.mixer.music.stop()
        except Exception: pass

    # ————— input —————
    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            k = e.key
            if k in (pygame.K_ESCAPE, pygame.K_q):
                self._stop_all_audio()
                from .menu import MenuScene
                self.app.scenes.switch(MenuScene)
                return
            if k == pygame.K_e and not self.answered:
                
                self.answered = True
                self._stop_ringing()
                self._play_message()
            elif k == pygame.K_r:
                
                self._stop_all_audio()
                self.answered = False
                self.playing_msg = False
                self._start_ringing()
            elif k == pygame.K_f:
                self.wobble = not self.wobble

    # ————— update/draw —————
    def update(self, dt):
        self.t += dt
        self.glitch_phase += dt * (1.0 if not self.answered else 2.0)

        # music.get_busy false is
        if self.playing_msg:
            try:
                if not pygame.mixer.music.get_busy():
                    self.playing_msg = False
            except Exception:
                self.playing_msg = False

    def draw(self, s):
        
        self.room.fill(BG)
        w, h = self.w, self.h
        cx, cy = w//2, int(h*0.58)

        
        #floor = pygame.Rect(0, cy, w, h-cy)
        #wall  = pygame.Rect(0, int(h*0.18), w, int(h*0.40))
        #pygame.draw.rect(self.room, (28, 30, 26), floor)
        #pygame.draw.rect(self.room, (24, 22, 24), wall)

        
        #desk_h = int(h*0.10)
        #desk = pygame.Rect(int(w*0.18), int(h*0.58), int(w*0.64), desk_h)
        #pygame.draw.rect(self.room, (40, 16, 16), desk)
        #pygame.draw.rect(self.room, (80, 36, 36), desk, 2)

        
        #cone = pygame.Surface((w, h), pygame.SRCALPHA)
        #for i in range(6):
           # a = max(0, 120 - i*18)
            #pygame.draw.polygon(
               # cone, (120, 20, 20, a),
                #[(cx, int(h*0.22)),
                 #(int(w*0.12), int(h*0.70 + i*3)),
                 #(int(w*0.88), int(h*0.70 + i*3))]
           # )
        #self.room.blit(cone, (0,0), special_flags=pygame.BLEND_ADD)
        
        if self.phone_img:
            r = self.phone_img.get_rect(center=(cx, int(h*0.56)))
            self.room.blit(self.phone_img, r)
        else:
            base = pygame.Rect(cx-90, int(h*0.53), 180, 40)
            pygame.draw.rect(self.room, (160, 20, 20), base, border_radius=10)
            pygame.draw.rect(self.room, (210, 40, 40), base, 2, border_radius=10)
            handset = pygame.Rect(cx-120, int(h*0.50), 240, 22)
            pygame.draw.rect(self.room, (200, 32, 32), handset, border_radius=11)
            pygame.draw.rect(self.room, (240, 60, 60), handset, 2, border_radius=11)

        
        if self.wobble:
            wsurf = pygame.Surface((w, h), pygame.SRCALPHA)
            for y in range(h):
                
                off = int(2 * math.sin((y*0.03) + self.t*3.2))
                wsurf.blit(self.room, (off, y), area=pygame.Rect(0, y, w, 1))
            s.blit(wsurf, (0,0))
        else:
            s.blit(self.room, (0,0))

        # scanline
        s.blit(self.scan, (0,0))
        vignette = pygame.Surface((w,h), pygame.SRCALPHA)
        pygame.draw.rect(vignette, (0,0,0,90), s.get_rect(), border_radius=0)
        s.blit(vignette, (0,0), special_flags=pygame.BLEND_RGBA_SUB)

        # UI
        title = "HOTLINE CHAMBER"
        draw_text(s, title, 28, ACCENT, topleft=(24, 18))
        if not self.answered:
            msg = "Phone is ringing…  [E] Answer   [R] Reset   [F] Toggle wobble   [ESC] Back"
        else:
            msg = "Listening…  [R] Replay   [F] Toggle wobble   [ESC] Back"
        draw_text(s, msg, 18, MUTED, topleft=(24, 50))

        # Glitchy effect
        if self.answered and (int(self.t*3) % 2 == 0):
            draw_text(s, "RECEIVING TRANSMISSION…", 18, (200,60,60),
                      topleft=(24 + int(2*math.sin(self.t*8.0)), 78))

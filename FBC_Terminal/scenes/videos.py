# -*- coding: utf-8 -*-
import os, tempfile
import pygame

try:
    import cv2  # OpenCV
except Exception:
    cv2 = None

from ..settings import BG, FG, MUTED, ACCENT, TITLE_TEXT, LOGO_PATH, VIDEOS_DIR
from ..core.scene import Scene
from ..utils.gfx import draw_text, draw_header_with_right_logo, draw_pulsing_highlight
from ..utils.audio import get_ffmpeg_exe, extract_audio_to_wav, find_sidecar_wav  # utils/audio.py

# --------- Helpers ---------
def list_videos():
    if not os.path.isdir(VIDEOS_DIR):
        return []
    exts = (".mp4", ".MP4", ".mov", ".MOV", ".m4v", ".M4V")
    files = [os.path.join(VIDEOS_DIR, n) for n in sorted(os.listdir(VIDEOS_DIR)) if n.endswith(exts)]
    return files

# --------- List of Content Pages ---------
class VideosList(Scene):
    def enter(self):
        self.files = list_videos()
        self.sel = 0
        self.line_h = pygame.font.SysFont("consolas,monospace", 24).get_height() + 6

    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                from .menu import MenuScene
                self.app.scenes.switch(MenuScene)
            elif self.files:
                if e.key in (pygame.K_UP, pygame.K_w):
                    self.sel = max(0, self.sel - 1)
                elif e.key in (pygame.K_DOWN, pygame.K_s):
                    self.sel = min(len(self.files) - 1, self.sel + 1)
                elif e.key in (pygame.K_RETURN, pygame.K_SPACE):
                    path = self.files[self.sel]
                    self.app.scenes.switch(lambda app: VideoPlayerScene(app, path))
                elif e.key == pygame.K_F11:
                    self.app.toggle_fullscreen()

    def draw(self, s):
        s.fill(BG)
        content = draw_header_with_right_logo(
            s, TITLE_TEXT, logo_path=LOGO_PATH, logo_scale_h=0.52, top_pad=36, side_pad=40
        )
        draw_text(s, "Videos", 22, FG, topleft=(content.left, content.top - 8))
        draw_text(s, "Enter/Space: play • SPACE pause • F fit mode • ESC back",
                  18, MUTED, topleft=(content.left, content.top + 20))

        if cv2 is None:
            draw_text(s, "OpenCV not available — pip install opencv-python", 22, ACCENT,
                      topleft=(content.left, content.top + 60))
            return

        if not self.files:
            draw_text(s, f"No video files in {VIDEOS_DIR}", 22, ACCENT,
                      topleft=(content.left, content.top + 60))
            return

        import math
        t = pygame.time.get_ticks() / 1000.0
        pulse = 60 + int(60 * (0.5 + 0.5 * math.sin(t * 6)))

        y = content.top + 48
        area_h = content.bottom - y
        max_lines = max(1, area_h // self.line_h)
        start = max(0, self.sel - max_lines // 2)
        end   = min(len(self.files), start + max_lines)

        for i in range(start, end):
            name = os.path.basename(self.files[i])
            if i == self.sel:
                rect = pygame.Rect(content.left - 8, y - 2, content.width + 8, self.line_h)
                draw_pulsing_highlight(s, rect, pulse)
                draw_text(s, "▸", 24, FG, topleft=(content.left - 4, y)); color = FG
            else:
                color = ACCENT
            draw_text(s, name, 24, color, topleft=(content.left + 18, y))
            y += self.line_h

# --------- VideoPlayer ---------
class VideoPlayerScene(Scene):
    """
    Video: OpenCV ile frame çizimi
    Audio: sidecar WAV (same-name.wav) veya ffmpeg ile çıkarılan geçici WAV
    """
    def __init__(self, app, path):
        super().__init__(app)
        self.path = path
        self.cap = None
        self.frame_surf = None
        self.accum = 0.0
        self.fps = 30.0
        self.ended = False
        self.paused = False
        self.fit_mode = 0  # 0 both, 1 fit width, 2 fit height

        # audio
        self.audio_wav = None
        self.sidecar_used = False
        self.has_audio = False
        self.length_sec = None

    def enter(self):
        if cv2 is None:
            from .videos import VideosList
            self.app.push_info("OpenCV not available.")
            self.app.scenes.switch(VideosList)
            return

        # Video init
        self.cap = __import__("cv2").VideoCapture(self.path)
        if not self.cap.isOpened():
            from .videos import VideosList
            self.app.push_info("Cannot open video.")
            self.app.scenes.switch(VideosList)
            return

        fps = self.cap.get(__import__("cv2").CAP_PROP_FPS)
        if fps and fps > 1:
            self.fps = float(fps)
        total_frames = self.cap.get(__import__("cv2").CAP_PROP_FRAME_COUNT) or 0
        self.length_sec = (total_frames / self.fps) if self.fps > 0 else None
        self._read_frame()  # first frame

        # Audio init (priority: sidecar WAV -> ffmpeg -> none)
        self._init_audio()

    # --- audio helpers ---
    def _init_audio(self):
        self.has_audio = False
        self.sidecar_used = False

        # 1) sidecar .wav?
        sidecar = find_sidecar_wav(self.path)
        if sidecar and os.path.exists(sidecar):
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(sidecar)
                pygame.mixer.music.play()
                self.has_audio = True
                self.sidecar_used = True
                return
            except Exception:
                self.has_audio = False

        # 2) ffmpeg extraction
        ff = get_ffmpeg_exe()
        if ff:
            try:
                tmpdir = tempfile.gettempdir()
                base = os.path.splitext(os.path.basename(self.path))[0]
                self.audio_wav = os.path.join(tmpdir, f"{base}_tmp_audio.wav")
                ok = extract_audio_to_wav(self.path, self.audio_wav, ff)
                if ok:
                    if not pygame.mixer.get_init():
                        pygame.mixer.init()
                    pygame.mixer.music.load(self.audio_wav)
                    pygame.mixer.music.play()
                    self.has_audio = True
                else:
                    self.audio_wav = None
            except Exception:
                self.has_audio = False

        if not self.has_audio:
            self.app.push_info("Audio muted: add sidecar WAV or install ffmpeg")

    # --- video helpers ---
    def _read_frame(self):
        ok, frame = self.cap.read()
        if not ok:
            self.ended = True
            return
        frame = __import__("cv2").cvtColor(frame, __import__("cv2").COLOR_BGR2RGB)

        sw, sh = self.app.screen.get_size()
        target_w, target_h = int(sw * 0.9), int(sh * 0.9)
        fh, fw = frame.shape[0], frame.shape[1]
        if self.fit_mode == 1:
            scale = target_w / fw
        elif self.fit_mode == 2:
            scale = target_h / fh
        else:
            scale = min(target_w / fw, target_h / fh)

        new_w, new_h = max(1, int(fw * scale)), max(1, int(fh * scale))
        frame = __import__("cv2").resize(frame, (new_w, new_h), interpolation=__import__("cv2").INTER_AREA)
        # OpenCV array -> pygame surface
        self.frame_surf = pygame.surfarray.make_surface(frame.swapaxes(0, 1)).convert()

    # --- scene io ---
    def handle(self, e):
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                self.cleanup()
                from .videos import VideosList
                self.app.scenes.switch(VideosList)
            elif e.key == pygame.K_SPACE:
                self.paused = not self.paused
                if self.has_audio:
                    try:
                        if self.paused:
                            pygame.mixer.music.pause()
                        else:
                            pygame.mixer.music.unpause()
                    except Exception:
                        pass
            elif e.key == pygame.K_f:
                self.fit_mode = (self.fit_mode + 1) % 3

    def update(self, dt):
        if self.ended or self.cap is None or self.paused:
            return
        self.accum += dt
        interval = 1.0 / self.fps if self.fps > 0 else 1 / 30
        while self.accum >= interval:
            self.accum -= interval
            self._read_frame()
            if self.ended:
                if self.has_audio:
                    try: pygame.mixer.music.stop()
                    except Exception: pass
                break

    def draw(self, s):
        s.fill(BG)
        if self.frame_surf:
            rect = self.frame_surf.get_rect(center=s.get_rect().center)
            s.blit(self.frame_surf, rect)
            overlay = pygame.Surface(s.get_size()).convert_alpha()
            overlay.fill((0, 180, 0, 40))
            s.blit(overlay, (0, 0))

        name = os.path.basename(self.path)
        draw_text(s, name, 20, FG, topleft=(20, 14))
        draw_text(s, "SPACE: pause • F: fit mode • ESC: back", 18, MUTED, topleft=(20, 42))
        if self.length_sec:
            m = int(self.length_sec // 60); sec = int(self.length_sec % 60)
            draw_text(s, f"Duration: {m:02d}:{sec:02d}", 18, MUTED, topleft=(20, 64))
        if self.has_audio:
            src = "WAV" if self.sidecar_used else "ffmpeg"
            draw_text(s, f"Audio: {src}", 16, MUTED, topleft=(20, 84))
        else:
            draw_text(s, "Audio: off", 16, MUTED, topleft=(20, 84))

    def cleanup(self):
        try:
            if self.cap is not None:
                self.cap.release()
        except Exception:
            pass
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        try:
            if self.audio_wav and os.path.exists(self.audio_wav):
                os.remove(self.audio_wav)
        except Exception:
            pass

    def exit(self):
        self.cleanup()

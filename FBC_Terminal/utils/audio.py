import os, math, shutil, tempfile, subprocess
import pygame

def make_beep_sequence(beep_ms=150, pause_ms=150, count=3, freq=880, volume=0.3, rate=44100):
    if not pygame.mixer.get_init():
        pygame.mixer.init()
    from array import array
    samples = array("h")
    n_beep  = int(rate * (beep_ms/1000.0))
    n_pause = int(rate * (pause_ms/1000.0))
    amp = int(32767 * volume)
    for _ in range(count):
        for i in range(n_beep):
            t = i / rate
            sample = int(amp * math.sin(2*math.pi*freq*t))
            samples.append(sample)
        for _ in range(n_pause):
            samples.append(0)
    return pygame.mixer.Sound(buffer=samples.tobytes())

def make_beep(freq=880, ms=120, volume=0.22, rate=44100):
    try:
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        n = int(rate * (ms/1000.0))
        amp = int(32767 * volume)
        from array import array
        buf = array("h", (int(amp * math.sin(2*math.pi*freq*(i/rate))) for i in range(n)))
        return pygame.mixer.Sound(buffer=buf.tobytes())
    except Exception:
        return None

def get_ffmpeg_exe():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        pass
    exe = shutil.which("ffmpeg")
    return exe

def transcode_to_temp_wav(src_path, rate=44100, ch=2):
    exe = get_ffmpeg_exe()
    if not exe or not os.path.exists(src_path):
        return None
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
    tmp_path = tmp.name
    tmp.close()
    cmd = [exe, "-y", "-i", src_path, "-vn", "-acodec", "pcm_s16le", "-ar", str(rate), "-ac", str(ch), tmp_path]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return tmp_path if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0 else None
    except Exception:
        try: os.remove(tmp_path)
        except Exception: pass
        return None

def find_sidecar_wav(video_path):
    base, _ = os.path.splitext(video_path)
    cand = base + ".wav"
    return cand if os.path.exists(cand) else None

def extract_audio_to_wav(video_path, out_wav, ffmpeg_exe):
    if not ffmpeg_exe:
        return False
    cmd = [ffmpeg_exe, "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
           "-ar", "44100", "-ac", "2", out_wav]
    try:
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        return os.path.exists(out_wav) and os.path.getsize(out_wav) > 0
    except Exception:
        return False

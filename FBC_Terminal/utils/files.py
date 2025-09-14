import os, glob
from ..settings import VIDEOS_DIR, AUDIOS_DIR, ALTERED_DIR, OOP_DIR

def safe_read_text(path, fallback="(missing)"):
    try:
        if not path: return fallback
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            t = f.read().strip()
            return t if t else fallback
    except Exception:
        return fallback

def list_videos():
    if not os.path.isdir(VIDEOS_DIR):
        return []
    out = []
    for p in sorted(glob.glob(os.path.join(VIDEOS_DIR, "*.mp4"))) + sorted(glob.glob(os.path.join(VIDEOS_DIR, "*.MP4"))):
        if p not in out: out.append(p)
    return out

def list_audio_logs():
    if not os.path.isdir(AUDIOS_DIR):
        return []
    mp3s = {}
    for p in glob.glob(os.path.join(AUDIOS_DIR, "*.mp3")) + glob.glob(os.path.join(AUDIOS_DIR, "*.MP3")):
        base = os.path.splitext(os.path.basename(p))[0]
        mp3s[base] = p
    out = []
    for p in glob.glob(os.path.join(AUDIOS_DIR, "*.txt")) + glob.glob(os.path.join(AUDIOS_DIR, "*.TXT")):
        base = os.path.splitext(os.path.basename(p))[0]
        if base in mp3s:
            out.append((base, mp3s[base], p))
    out.sort()
    return out

def list_altered_items():
    """Return list of dicts: {code, dates, info, image}"""
    items = []
    if not os.path.isdir(ALTERED_DIR):
        return items
    for code in sorted(os.listdir(ALTERED_DIR)):
        folder = os.path.join(ALTERED_DIR, code)
        if not os.path.isdir(folder): continue
        dates = os.path.join(folder, "dates.txt")
        info  = os.path.join(folder, "info.txt")
        image = os.path.join(folder, "image.png")
        items.append({"code": code, "dates": dates, "info": info, "image": image if os.path.exists(image) else None})
    return items

def list_oop_items():
    items = []
    if not os.path.isdir(OOP_DIR):
        return items
    for code in sorted(os.listdir(OOP_DIR)):
        folder = os.path.join(OOP_DIR, code)
        if not os.path.isdir(folder): continue
        dates = os.path.join(folder, "dates.txt")
        info  = os.path.join(folder, "info.txt")
        image = os.path.join(folder, "image.png")
        items.append({"code": code, "dates": dates, "info": info, "image": image if os.path.exists(image) else None})
    return items

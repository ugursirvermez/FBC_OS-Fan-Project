# Federal Bureau of Control — Terminal OS (FBC OS)

<img width="360" height="360" alt="Logo" src="https://github.com/user-attachments/assets/33a868ee-80d2-4d35-80d6-fd8899b4a8c8" />


A retro-styled **fictional operating system**, inspired by *Remedy’s Control* universe.  This project simulates what an internal FBC computer terminal could look and feel like:  CRT aesthetics, documents, audio logs, hotline archives, maps, altered items…  
It is both a **playable lore archive** and an **interactive fan experiment**. **A strange terminal for a stranger house.**
---

## ✨ Features

- **Splash / Lock / Warning screens** with CRT-style animations  
- **Main Menu** including:
  - 📂 Documents viewer (PDFs inside the Bureau’s archive)  
  - 🎬 Video logs player (MP4 with sound)  
  - 🎧 Audio logs with synced transcripts  
  - 🗺️ Maps of the Oldest House  
  - 📦 Altered Items archive (dates, info, images)  
  - 🔮 Objects of Power archive (TOP SECRET dossiers)  
  - ☎️ Hotline — including a Hotline phone overlay  
  - 🏗️ Oceanview Motel & Casino (experimental 3D raycasting mini-scene)  
- **Overlays / Events**
  - Ahti overlay with music toggle  
  - Threshold events with randomized full-screen alerts  
  - Decrypt overlay (puzzle-like unlock effect)  
- **Mini-game:** Black Rock Quarry extraction simulation  
- **Global keyboard sounds** for every input  
- **Warning / INFO bars** for immersion
---
## 🗂️ Project Organization

- **app.py** → Main entry point  
- **settings.py** → Global configuration (fullscreen, CRT alpha, etc.)  
- **scenes/** → Menu, documents, audio, maps, Oceanview, etc.  
- **overlays/** → Ahti, Threshold, Decrypt overlays  
- **utils/** → Helpers (audio, gfx, text rendering)  
- **content/** → Game data (pdf, mp3, json…)  
- **assets/** → Logos, icons, hotline phone graphic, etc.

---

## 🔧 Requirements

- Python 3.10 or later  
- Dependencies:  
```bash
pip install pygame moviepy pyfiglet pymupdf opencv-python mutagen imageio-ffmpeg
```
## 🚀 How to Run
1. **Clone the repo:**
```bash
git clone https://github.com/yourname/fbc-os.git
cd fbc-os
 ```
2. **Download the Assets folder (logos, hotline phone, etc.) from the shared Google Drive link:**
👉 [Download Assets](https://drive.google.com/drive/folders/15TDk7GEFRfWJN1hwmbqkIn3JHL_cZNVq?usp=sharing)

Place it into the project root so that your folder looks like: \
fbc-os/ \
   ├── assets/ \
   ├── FBC_Terminal/ \
   ├── main.py \
   ├── requirements.txt \
   
3. **Start the terminal:**
```bash
python app.py
```
## 🕹️ Controls
- Arrows / Enter → Navigate menus
- Esc → Back / Quit
- J → Toggle Ahti overlay
- Any key → Key click sound feedback
- Audio Logs → Transcript highlights sync with playback
- Oceanview Motel → WASD + mouse to move/look

## 📜 Notes
This is a fan project — all rights for Control and the Remedy Connected Universe belong to Remedy Entertainment.
Shared purely for academic and fan-artistic purposes.
Assets (audio, video, imagery) are not redistributed on GitHub, only via a private Google Drive link.

## 🛠️ Development Notes
Modular Python/Pygame structure, split into scenes, overlays, and utils. Adding new content is as easy as dropping PDFs, MP3s, or JSON files into assets/
Experiments include:
- CRT scanline overlays
- Audio-transcript synchronization
- 3D raycasting (Wolfenstein-style) for Oceanview Motel prototype

## ❤️ Contribution

This is a passion project. Feel free to fork, suggest ideas, or build on top.
Bug reports and pull requests are welcome.

## 📹 Screenshots
![1](https://github.com/user-attachments/assets/30288e66-73a6-4fb3-886e-9b9b7be0be8c)
![2](https://github.com/user-attachments/assets/ee5b37f1-5cb4-47b4-8295-289897571a49)
![3](https://github.com/user-attachments/assets/433cd95a-52a3-4b86-8a20-10736ffe21ed)
![4](https://github.com/user-attachments/assets/7b2bd30f-5e71-4653-ada8-24381e02f057)




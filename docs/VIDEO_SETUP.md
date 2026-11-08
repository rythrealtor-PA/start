# Video setup: Claude + Chatterbox + faster-whisper + Blender

All four tools are free. Here's what each one does:

| Tool | Job in the video | Where it runs |
|---|---|---|
| **Chatterbox TTS** (Resemble AI) | Turns a script into a natural voiceover, can clone **your** voice from a 10 s clip | Your computer (GPU strongly recommended) |
| **faster-whisper** | Turns audio into captions with word-level timing, so visuals and captions line up with the voice | Your computer (CPU is fine) |
| **Blender + MCP for Blender** | Lets Claude build and animate 3D scenes (house tours, product shots, animated text) and render them | Your computer, Blender must be open |
| **ffmpeg** | Joins render + voice + captions + music into the final MP4 | Your computer |

> **Important:** Blender MCP talks to the Blender window on **your** computer. It works when you run
> Claude **locally**: Claude Desktop, or Claude Code in your terminal or VS Code. A cloud session
> (claude.ai/code on the web or phone) can't see your Blender. It can still make voiceovers and
> captions, but it can't drive Blender.

---

## Step 1: Install the basics (one time)

**Python 3.11** (best match for Chatterbox), **ffmpeg**, **uv**, **Blender 4.2+**, and **git**.

**Windows** (PowerShell):
```powershell
winget install Python.Python.3.11
```
```powershell
winget install Gyan.FFmpeg
```
```powershell
winget install --id=astral-sh.uv -e
```
```powershell
winget install BlenderFoundation.Blender
```

**Mac** (install [Homebrew](https://brew.sh) first):
```bash
brew install python@3.11 ffmpeg uv
```
```bash
brew install --cask blender
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt install python3.11 python3.11-venv ffmpeg git
```
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```
Then download Blender from https://www.blender.org/download/.

Close and reopen your terminal afterwards so the new commands are found.

## Step 2: Get this repo onto your computer

```bash
git clone https://github.com/rythrealtor-PA/start.git
```
```bash
cd start
```

## Step 3: Install Chatterbox and faster-whisper

Make a Python environment just for this:

```bash
uv venv --python 3.11 .venv
```

Activate it. **Mac/Linux:**
```bash
source .venv/bin/activate
```
**Windows:**
```powershell
.venv\Scripts\activate
```

**If you have an NVIDIA graphics card** (Windows/Linux), install the GPU build of PyTorch first.
It makes voiceovers about 10x faster:
```bash
uv pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
```

Then everyone runs:
```bash
uv pip install -r video-tools/requirements.txt
```

Macs with Apple Silicon (M1–M4) are detected automatically and use the Mac GPU.

The first run downloads the AI models (Chatterbox about 2–3 GB, Whisper "small" about 500 MB). They're stored
in your Hugging Face cache, so later runs start quickly.

**Test it:**
```bash
python video-tools/tts.py --text "Hi, this is my first AI voiceover." --out out/test.wav
```
```bash
python video-tools/transcribe.py out/test.wav
```
You should get `out/test.wav` plus `out/test.srt`, `.vtt`, `.json` and `.txt`.

**Use your own voice:** record yourself talking naturally for 10–15 seconds in a quiet room
(phone voice memo is fine), convert it to wav, and pass it with `--voice`:
```bash
ffmpeg -i my_voice_memo.m4a -ac 1 -ar 24000 me.wav
```
```bash
python video-tools/tts.py --voice me.wav --text "Welcome to 12 Oak Street." --out out/oak.wav
```
Only clone your own voice, or a voice you have permission to use.

## Step 4: Connect Blender to Claude

**Easiest way:** run one command. It finds Claude Desktop / Claude Code and installs the Blender addon for you:

Mac/Linux:
```bash
uvx mcp-for-blender setup
```
Windows (PowerShell):
```powershell
uvx mcp-for-blender setup
```

**Or do it by hand:**

1. Install the Blender addon:
   ```bash
   uvx mcp-for-blender install-addon
   ```
   Then in Blender go to **Edit → Preferences → Add-ons** and enable **Interface: MCP for Blender**.
2. Tell Claude about it:
   - **Claude Code:** nothing to do. This repo has a `.mcp.json` that adds the `blender` server
     automatically. Claude Code asks you to approve it the first time you open the folder. Or add it
     everywhere with:
     ```bash
     claude mcp add blender uvx mcp-for-blender
     ```
   - **Claude Desktop:** Settings → Developer → Edit Config, and add:
     ```json
     {
       "mcpServers": {
         "blender": { "command": "uvx", "args": ["mcp-for-blender"] }
       }
     }
     ```
     Then **fully quit** Claude Desktop (on Windows, quit it from the system tray too) and reopen it.
3. Open Blender, press **N** in the 3D viewport, open the **MCP for Blender** tab, and click
   **Start MCP Server** if it isn't running already. Tick **Poly Haven** to get free HDRIs, textures and models.

**Test it:** in Claude, ask *"Use Blender to make a simple living room with a sofa and a window, then show me the camera view."*

## Step 5: Check everything

```bash
python video-tools/check_setup.py
```

Every line should say `OK` (Blender must be open for the last check).

## Step 6: Make videos

Open Claude Code in this folder:
```bash
claude
```
Then just ask, for example:

- *"Make a 30-second vertical reel for 12 Oak Street: 3 bed, 2 bath, renovated kitchen. Use my voice from me.wav."*
- *"Build a 3D animated intro with my name and 'Your Local Realtor', 5 seconds, then add voiceover and captions."*
- *"Add captions to walkthrough.mp4 and export a 1080x1920 version."*

The `video-production` skill in `.claude/skills/` tells Claude the whole pipeline:
script → Chatterbox voiceover → faster-whisper timing → Blender scene timed to the words → ffmpeg final.

You can also run the steps yourself:
```bash
python video-tools/tts.py --file script.txt --voice me.wav --out out/vo.wav
```
```bash
python video-tools/transcribe.py out/vo.wav --max-words 3
```
```bash
python video-tools/assemble.py --visual renders/tour.mp4 --audio out/vo.wav --subs out/vo.srt --size 1080x1920 --out out/final.mp4
```

---

## Troubleshooting

| Problem | Fix |
|---|---|
| No hammer/Blender tools in Claude | Fully quit and reopen Claude. Check `uvx` works in a fresh terminal. Run `claude mcp list` (Claude Code). |
| "Could not connect to Blender" | Blender isn't open, or the server isn't started: press N, **MCP for Blender** tab, **Start MCP Server**. Port is 9876. |
| Timeouts while Blender renders | Ask Claude to render a few test frames, then render the full animation yourself with **Ctrl+F12**. |
| Voiceover is very slow | You're on CPU. Install the GPU PyTorch (Step 3), or use `--model turbo` with `--voice`. |
| `CUDA out of memory` | Close other apps/games, or use `--model turbo` (smaller model). |
| Voice sounds rushed | `--cfg-weight 0.3`. For more emotion add `--exaggeration 0.7`. |
| Captions missing in final video | Your ffmpeg lacks libass. Install the full ffmpeg build (winget `Gyan.FFmpeg`, brew `ffmpeg`). |
| Wrong words in captions | Use a bigger model: `--model medium` or `--model large-v3`, and set `--lang en`. |

Links: [Chatterbox](https://github.com/resemble-ai/chatterbox) · [faster-whisper](https://github.com/SYSTRAN/faster-whisper) · [MCP for Blender](https://github.com/ahujasid/mcp-for-blender) · [Blender](https://www.blender.org)

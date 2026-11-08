---
name: video-production
description: Make videos end to end with free local tools - Chatterbox TTS for voiceover, faster-whisper for captions and timing, Blender (via the MCP for Blender server) for 3D scenes and renders, and ffmpeg to assemble. Use when the user asks for a video, reel, short, TikTok, YouTube clip, listing/property tour, explainer, voiceover, narration, captions/subtitles, transcription, or a Blender scene/animation/render.
---

# Video Production

Pipeline: **script → voiceover (Chatterbox) → timing (faster-whisper) → visuals (Blender MCP) → assemble (ffmpeg)**.
Scripts live in `video-tools/`. Setup instructions for the user are in `docs/VIDEO_SETUP.md`.

## 0. Check what's available first

```bash
python video-tools/check_setup.py
```

- Blender tools show up as `mcp__blender__*` only when the user runs Claude **on the same computer as Blender**
  (Claude Desktop or Claude Code locally) with Blender open and the addon server started.
  In a cloud session there is no Blender: say so, and still deliver voiceover + captions + an assembled
  video from images or clips the user provides.
- Chatterbox runs on CPU but slowly (often 10x+ real time). With no GPU, keep drafts short and tell the user.

## 1. Script

Write for the ear: short sentences, one idea each, ~150 words per minute
(a 30 s reel ≈ 75 words, 60 s ≈ 150). Hook in the first sentence. Save to `out/<project>/script.txt`.
Show the script to the user before generating audio for anything longer than ~30 s.

## 2. Voiceover - `video-tools/tts.py`

```bash
python video-tools/tts.py --file out/<project>/script.txt --out out/<project>/voiceover.wav
```

| Need | Flags |
|---|---|
| User's own voice | `--voice path/to/their_10s_clip.wav` |
| Faster, English, `[laugh]` `[chuckle]` tags | `--model turbo --voice clip.wav` |
| Other languages (23) | `--model multilingual --lang es` |
| More energetic / dramatic | `--exaggeration 0.7 --cfg-weight 0.3` |
| Calmer, slower | `--exaggeration 0.4 --cfg-weight 0.3` |

Only clone a voice the user owns or has permission to use. Never imitate a real public figure.

## 3. Timing + captions - `video-tools/transcribe.py`

```bash
python video-tools/transcribe.py out/<project>/voiceover.wav --max-words 3     # vertical shorts
python video-tools/transcribe.py out/<project>/voiceover.wav                   # landscape / YouTube
```

Produces `.srt`, `.vtt`, `.txt`, and `.json`. **Use the `.json` word timestamps to plan the visuals**:
each sentence/segment becomes a shot, and its `start`/`end` (seconds × fps) become Blender keyframe frames.
Also use it to check the TTS read the script correctly (compare `.txt` to the script).
It also transcribes any user-supplied video/audio (interviews, walkthrough clips).

## 4. Visuals - Blender via MCP

Tools (MCP for Blender 2.x): `get_addon_status`, `get_scene_info`, `execute_blender_code` (run bpy Python),
`look` (view the result: `viewport`, `camera`, `angles`, `frames` strip, or a render/image file),
`search_assets` / `import_asset` (Poly Haven CC0 HDRIs/textures/models - free, tick **Poly Haven** in the
addon panel; Sketchfab and Poly Pizza too) and `generate_3d` (AI models - needs API keys or credits, so ask first).

Workflow:
1. `get_addon_status`, then `get_scene_info` - see what's there before changing anything.
2. Build in small steps with `execute_blender_code`; after each step call `look` (`camera` view) and check it.
   For lighting, prefer a Poly Haven HDRI via `search_assets`/`import_asset` over hand-placed lamps.
3. Set the scene to match the voiceover:
   ```python
   import bpy
   s = bpy.context.scene
   s.render.fps = 30
   s.frame_start, s.frame_end = 1, int(DURATION_SECONDS * 30)
   s.render.resolution_x, s.render.resolution_y = 1080, 1920   # or 1920x1080
   ```
4. Key camera moves / object animations on frames from the transcript JSON (`int(start * fps)`),
   then check motion with `look` using `frames`.
5. Render to a file the user can find:
   ```python
   s.render.engine = 'BLENDER_EEVEE_NEXT'   # fast; use 'CYCLES' for final quality (Blender 4.2+ name; older: 'BLENDER_EEVEE')
   s.render.image_settings.file_format = 'FFMPEG'
   s.render.ffmpeg.format = 'MPEG4'; s.render.ffmpeg.codec = 'H264'
   s.render.filepath = '//renders/scene.mp4'   # '//' = next to the .blend file
   bpy.ops.render.render(animation=True)
   ```
   Long renders can block the MCP connection; for anything over ~1 minute of frames, render a
   few test frames first, then tell the user the full render command or let them press Ctrl+F12.
   Save the .blend first (`bpy.ops.wm.save_as_mainfile(filepath=...)`) so `//` resolves.

## 5. Assemble - `video-tools/assemble.py`

```bash
python video-tools/assemble.py --visual renders/scene.mp4 --audio out/<project>/voiceover.wav \
  --subs out/<project>/voiceover.srt --size 1080x1920 --out out/<project>/final.mp4
```

`--visual` accepts a video, a folder of rendered frames, or one still image. Add `--music track.mp3`
for background music (only royalty-free music the user has rights to). Output length = voiceover length.

Sizes: Reels/TikTok/Shorts `1080x1920`, YouTube `1920x1080`, square feed `1080x1080`.

## 6. Check before handing over

```bash
ffprobe -v error -show_entries format=duration:stream=width,height,codec_name -of compact out/<project>/final.mp4
ffmpeg -y -ss 3 -i out/<project>/final.mp4 -frames:v 1 out/<project>/preview.jpg
```

Look at `preview.jpg` (captions readable, not cut off, framing right) before saying it's done.
Real estate content: no claims about a property you can't verify; include any brokerage
disclosure the user specifies.

# Light & Sound — Theater Edge

Python desktop foundation for a scene-aware audio theater, running on Windows.

## Run

From this folder in PowerShell:

```powershell
.\start.ps1
```

The launcher creates a local Python 3.11 environment and installs dependencies on
first run. If PowerShell blocks scripts, use the manual commands:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

The **Audio Theater** tab contains the movie player, scene analysis and terminal.
The **Ligh And Sound** tab is a placeholder for upcoming light and sound controls.

In **Audio Theater**, click **Browse MP4**, select a movie, then **Play**. Pause, stop, restart, seek and
volume controls are below the movie. Choose an OS audio output from the dropdown.
The movie path, volume, analysis switch, sampling interval, and output preference
are saved in `config.json` beside `main.py`, independent of the launch directory.
The next launch loads the same movie without automatically playing it.

## What works now

- Native Qt video playback with original movie audio on one selected device.
- Frame extraction from the playback decoder about every 750 ms; no separate
  decoder clock or unbounded analysis queue. Frames stay in memory.
- Background OpenCV frontal-face detection, annotated frame preview, and
  timestamped position messages in the app terminal and console.
- Eight screen-sector indicators: top, top-right, right, bottom-right, bottom,
  bottom-left, left, top-left. Center detections light all indicators equally.
- Recovery from missing movies and invalid configuration; bounded event log.

**The directional indicators are visual previews only.** They summarize visible
face positions, not identified audio sources, and do not route audio. A face is
not necessarily speaking. The initial detector does not detect cars, recognize
characters, maintain identities across frames, or separate voices/effects.
No detection means unknown sound position; the program does not invent a source.
Front-facing detection can miss small, occluded or side-facing faces.

## Path to moving-car spatial audio

1. Evaluate object detection/tracking on real movie clips, including cars and
   multiple people, camera cuts, and off-screen sound.
2. Preserve existing multichannel movie sound where available. For stereo movies,
   evaluate source separation and audio/visual association before panning an
   individual effect; otherwise music and dialogue move along with the effect.
3. Define physical speaker locations and implement smooth gain transitions,
   limiting, delay calibration and video/audio synchronization.
4. Validate eight actual output channels. A single multichannel audio interface
   offers a common clock. Eight Bluetooth USB dongles are not assumed to provide
   eight independent synchronized endpoints; actual adapters/speakers must be
   tested for driver support, latency and drift.

Screen top/bottom alone does not prove acoustic height; visible movement does not
prove that the object is making the sound. This project does not claim Dolby Atmos
rendering or guaranteed reconstruction of authored spatial audio from stereo.

## Verify

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Tests generate a temporary eight-second H.264/AAC MP4 and exercise actual Qt decode,
sampled-frame analysis, transport, configuration restore, stale-result rejection,
and Windows file release on close. Other tests cover malformed preferences and
screen direction/power mapping. No personal movie or downloaded AI model is needed.
Synthetic imagery proves integration, not face-detection accuracy on movies or
audible performance of physical speakers. Qt may print optional hardware codec
probe messages even while H.264 decoding succeeds.

Code modules: `theater/app.py` (UI/playback), `analysis.py` (worker), `spatial.py`
(screen positions/preview gains), and `config.py` (validated atomic settings).

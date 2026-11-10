# Theater Edge design

The goal is an entertainment system that eventually places individual movie sounds
around the listener, following sound sources such as moving cars.

The user delegated implementation choices and authorized proceeding without further
design questions. First deliverable: a Windows Python desktop movie player with
saved media path, playback controls, synchronized sampled frames, visible-face
position messages, and eight directional indicators around the movie.

## Approaches

1. Scene-guided remix of mixed movie audio: quick but moves dialogue and music
   together with effects. Do not present this as isolated object audio.
2. Decode existing surround tracks: preserves authored direction where available;
   cannot infer separate objects from ordinary stereo.
3. Separate sound sources and associate them with tracked visual objects: best fit
   for the long-term goal but requires model evaluation and synchronization work.

Build a modular foundation for approaches 2 and 3. Use Qt multimedia for actual
playback and audio output selection; sample its decoded frames directly, avoiding
a second playback clock. OpenCV face detection is an initial visible-character
locator only, never active-speaker identification. No car detector is claimed.

## First version

Python 3.11+, PySide6, OpenCV and NumPy. A central player, directional surround
preview, transport and volume, an analysis panel with bounding boxes, and a
bounded visible event log mirrored to the terminal. Save local settings atomically
to repository-root config.json. Missing media and malformed configuration must be
recoverable. Analysis runs off the UI thread, with at most one frame in flight.
Ignore results after source changes, seeking, stopping, or disabling analysis.

Eight indicators represent top, top-right, right, bottom-right, bottom, bottom-left,
left, top-left screen sectors. These are screen positions, not established physical
speaker locations. A centered detection has no directional preference. Explicitly
label indicators as visual previews, not routed audio. Audio goes to one selected
OS audio endpoint in this release. Device changes refresh the output list.

## Future work and constraints

Car/person tracking, active-speaker detection, sound separation, multichannel
rendering, room layout, gain/delay calibration, and Bluetooth endpoint validation.
Do not assume eight Bluetooth radios create eight synchronized playback endpoints.
Recommend a single multichannel device for a common clock; evaluate actual hardware
before committing to a transport. Screen coordinates cannot establish behind-the-
listener or physical elevation without additional scene interpretation.

## Validation

Unit tests for configuration recovery and position/gain mapping. Qt integration
test with generated moving imagery and audio checks decode, frame sampling,
pause/seek/stop, stale-result handling, and saved source restoration. Launch the
desktop application. Physical eight-speaker performance remains unverified.

# First milestone verification

Final result: 9 tests passed. Generated-movie desktop smoke extracted 5 frames;
native Windows UI inspection confirmed visible central playback and frame preview.
Application left open, paused on the generated test MP4. Dependency consistency,
PowerShell launcher syntax, and git whitespace checks passed.

- Config and spatial tests first failed on absent implementation, then passed.
- Real H.264/AAC generated-movie integration exercised frame sampling, pause,
  seek, stop, restore, and rejecting results from an obsolete source epoch.
- Windows file-release test reproduced WinError 32 after close; clearing the Qt
  media source before shutdown fixes it.
- Independent final review found missing keyboard/page-step seeking and inability
  to retry failed launcher installation. Added a failing real-player seek test,
  connected user slider actions, and moved dependency installation outside the
  environment-creation condition.
- Scope decision: first milestone is visible-face positions only, with one real
  movie audio endpoint. No individual sound separation, car detection, active
  speaker identification, physical elevation inference or eight-speaker routing.
- Visible-face accuracy on real movies and physical audio delivery require further
  evaluation. Generated MP4 tests prove decoder/worker integration only.

"""Generate a non-personal demo and capture our own rendered player for QA."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import imageio_ffmpeg
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from theater.app import TheaterWindow

folder = ROOT / '.test-artifacts'
folder.mkdir(exist_ok=True)
movie = folder / 'demo.mp4'
subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-f', 'lavfi', '-i',
                'testsrc2=size=960x540:rate=24', '-f', 'lavfi', '-i',
                'sine=frequency=440:sample_rate=48000', '-t', '8', '-c:v',
                'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac', str(movie)],
               check=True, capture_output=True)
app = QApplication([])
window = TheaterWindow(folder / 'preview-config.json')
window.show()
window.open_movie(movie)
window.player.play()


def finish():
    window.player.pause()
    window.grab().save(str(folder / 'player-preview.png'))
    print(f'Smoke check: {window.analyzed_frames} extracted frames; '
          f'position {window.player.position()} ms', flush=True)
    passed = window.analyzed_frames >= 2 and window.player.position() >= 1000
    window.close()
    app.exit(0 if passed else 1)


QTimer.singleShot(3500, finish)
sys.exit(app.exec())

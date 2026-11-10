"""Real decoder integration against a generated MP4; no personal media needed."""
import os
import subprocess
import tempfile
import time
import unittest
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtWidgets import QApplication, QAbstractSlider
from PySide6.QtMultimedia import QMediaPlayer
import imageio_ffmpeg
from theater.app import TheaterWindow
from theater.config import load_config


def spin_until(predicate, seconds=8):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        QApplication.processEvents()
        if predicate():
            return True
        time.sleep(.02)
    return False


class PlayerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.application = QApplication.instance() or QApplication([])
        cls.folder = tempfile.TemporaryDirectory()
        cls.movie = Path(cls.folder.name) / 'moving test.mp4'
        subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-f', 'lavfi',
                        '-i', 'testsrc2=size=640x360:rate=24', '-f', 'lavfi',
                        '-i', 'sine=frequency=440:sample_rate=48000', '-t', '8',
                        '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-c:a', 'aac',
                        str(cls.movie)], check=True, capture_output=True)

    @classmethod
    def tearDownClass(cls):
        cls.folder.cleanup()

    def setUp(self):
        self.config = Path(self.folder.name) / f'{self._testMethodName}.json'
        self.window = TheaterWindow(self.config)
        self.window.show()

    def tearDown(self):
        self.window.close()
        QApplication.processEvents()

    def test_decode_extract_pause_seek_stop_restore(self):
        self.assertTrue(self.window.open_movie(self.movie))
        self.window.player.play()
        self.assertTrue(spin_until(lambda: self.window.analyzed_frames >= 1),
                        self.window.log_view.toPlainText())
        self.assertGreater(self.window.player.duration(), 7000)
        self.window.player.pause()
        self.assertEqual(self.window.player.playbackState(), QMediaPlayer.PausedState)
        self.window.seek_to(4000)
        self.assertTrue(spin_until(lambda: abs(self.window.player.position() - 4000) < 500))
        self.window.stop_movie()
        self.assertEqual(self.window.player.playbackState(), QMediaPlayer.StoppedState)
        self.assertEqual(self.window.player.position(), 0)
        self.assertEqual(load_config(self.config)['movie_path'], str(self.movie.resolve()))
        self.window.close()
        self.window = TheaterWindow(self.config)
        self.assertEqual(Path(self.window.player.source().toLocalFile()), self.movie.resolve())

    def test_close_releases_movie_file(self):
        self.window.open_movie(self.movie)
        self.window.player.play()
        self.assertTrue(spin_until(lambda: self.window.analyzed_frames > 0))
        self.window.close()
        moved = self.movie.with_suffix('.renamed.mp4')
        self.movie.rename(moved)
        moved.rename(self.movie)

    def test_keyboard_and_page_step_seek_movie(self):
        self.window.open_movie(self.movie)
        self.assertTrue(spin_until(lambda: self.window.player.duration() > 0))
        self.window.seek.setSingleStep(1000)
        self.window.seek.triggerAction(QAbstractSlider.SliderSingleStepAdd)
        self.assertTrue(spin_until(lambda: self.window.player.position() == 1000, seconds=1))
        self.window.seek.setPageStep(2000)
        self.window.seek.triggerAction(QAbstractSlider.SliderPageStepAdd)
        self.assertTrue(spin_until(lambda: self.window.player.position() == 3000, seconds=1))

    def test_missing_media_and_stale_analysis(self):
        self.assertFalse(self.window.open_movie(Path(self.folder.name) / 'missing.mp4'))
        self.window.open_movie(self.movie)
        epoch = self.window.epoch
        self.window.seek_to(1000)
        self.window.accept_analysis({'epoch': epoch, 'timestamp': 0, 'detections': [],
                                     'image': None, 'error': ''})
        self.assertEqual(self.window.analyzed_frames, 0)
        self.window.analysis_toggle.setChecked(False)
        self.assertFalse(load_config(self.config)['analysis_enabled'])


if __name__ == '__main__':
    unittest.main()

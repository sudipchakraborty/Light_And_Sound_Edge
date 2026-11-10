import json
import math
import tempfile
import unittest
from pathlib import Path

from theater.config import load_config, save_config
from theater.spatial import screen_position, preview_gains


class ConfigTests(unittest.TestCase):
    def test_defaults_for_missing_and_corrupt_config(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            self.assertEqual(load_config(path)['movie_path'], '')
            path.write_text('{broken', encoding='utf-8')
            self.assertEqual(load_config(path)['volume'], 70)
            path.write_text('[1, 2]', encoding='utf-8')
            self.assertEqual(load_config(path)['movie_path'], '')

    def test_round_trip_unicode_path_and_validate_values(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'config.json'
            save_config(path, {'movie_path': 'D:/Movies/বাংলা.mp4', 'volume': 38})
            self.assertEqual(load_config(path)['movie_path'], 'D:/Movies/বাংলা.mp4')
            self.assertEqual(load_config(path)['volume'], 38)
            path.write_text(json.dumps({'volume': -9, 'sample_interval_ms': 0,
                                        'movie_path': [], 'analysis_enabled': 'yes'}))
            result = load_config(path)
            self.assertEqual(result['volume'], 0)
            self.assertGreaterEqual(result['sample_interval_ms'], 200)
            self.assertEqual(result['movie_path'], '')
            self.assertIs(result['analysis_enabled'], True)


class SpatialTests(unittest.TestCase):
    def test_positions(self):
        for x, y, expected in [(0, .5, 'left'), (1, .5, 'right'), (.5, 0, 'top'),
                                (.5, 1, 'bottom'), (0, 0, 'top-left'),
                                (1, 1, 'bottom-right'), (.5, .5, 'center')]:
            self.assertEqual(screen_position(x, y), expected)

    def test_preview_power_and_direction(self):
        gains = preview_gains(0, .5)
        self.assertEqual(max(gains, key=gains.get), 'left')
        self.assertAlmostEqual(sum(g * g for g in gains.values()), 1)
        center = preview_gains(.5, .5)
        self.assertEqual(len(set(center.values())), 1)
        self.assertTrue(all(math.isfinite(g) for g in center.values()))

    def test_reject_nonfinite_coordinates(self):
        with self.assertRaises(ValueError):
            screen_position(float('nan'), .5)


if __name__ == '__main__':
    unittest.main()

"""Validated local preferences; writes replace the file atomically."""
import json
import os
import tempfile
from pathlib import Path

DEFAULTS = dict(movie_path='', volume=70, sample_interval_ms=750,
                analysis_enabled=True, audio_device_id='')


def validated(data):
    result = DEFAULTS.copy()
    if not isinstance(data, dict):
        return result
    for key in ('movie_path', 'audio_device_id'):
        if isinstance(data.get(key), str):
            result[key] = data[key]
    for key, low, high in [('volume', 0, 100), ('sample_interval_ms', 200, 10000)]:
        value = data.get(key)
        if isinstance(value, int) and not isinstance(value, bool):
            result[key] = max(low, min(high, value))
    if isinstance(data.get('analysis_enabled'), bool):
        result['analysis_enabled'] = data['analysis_enabled']
    return result


def load_config(path: Path):
    try:
        return validated(json.loads(Path(path).read_text(encoding='utf-8')))
    except (OSError, ValueError, UnicodeError):
        return DEFAULTS.copy()


def save_config(path: Path, data: dict):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=path.name, suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(descriptor, 'w', encoding='utf-8') as stream:
            json.dump(validated(data), stream, indent=2, ensure_ascii=False)
            stream.write('\n')
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)

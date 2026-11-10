"""Desktop movie player. Direction indicators do not route movie audio."""
import math
import time
from pathlib import Path
from PySide6.QtCore import Qt, QThread, Signal, QUrl
from PySide6.QtGui import QPixmap
from PySide6.QtMultimedia import QAudioOutput, QMediaDevices, QMediaPlayer
from PySide6.QtMultimediaWidgets import QVideoWidget
from PySide6.QtWidgets import (QMainWindow, QWidget, QLabel, QPushButton,
                               QFileDialog, QVBoxLayout, QHBoxLayout,
                               QGridLayout, QSlider, QPlainTextEdit, QCheckBox,
                               QComboBox, QSplitter, QGroupBox, QProgressBar, QTabWidget)
from .analysis import FrameAnalyzer
from .config import load_config, save_config
from .spatial import DIRECTIONS, preview_gains

ROOT = Path(__file__).resolve().parents[1]


def clock(milliseconds):
    seconds = max(0, int(milliseconds)) // 1000
    return f'{seconds // 3600:02}:{seconds // 60 % 60:02}:{seconds % 60:02}'


class TheaterWindow(QMainWindow):
    analyze_frame = Signal(object)

    def __init__(self, config_path=None):
        super().__init__()
        self.config_path = Path(config_path) if config_path else ROOT / 'config.json'
        self.settings = load_config(self.config_path)
        self.epoch = 0
        self.busy = False
        self.last_sample = 0.
        self.analyzed_frames = 0
        self.setWindowTitle('Light & Sound • Theater Edge')
        self.resize(1320, 860)
        self.player = QMediaPlayer(self)
        self.audio = QAudioOutput(self)
        self.player.setAudioOutput(self.audio)
        self.devices = QMediaDevices(self)
        self.build_ui()
        self.player.setVideoOutput(self.video)
        self.audio.setVolume(self.settings['volume'] / 100)
        self.thread = QThread(self)
        self.analyzer = FrameAnalyzer()
        self.analyzer.moveToThread(self.thread)
        self.analyze_frame.connect(self.analyzer.analyze)
        self.analyzer.completed.connect(self.accept_analysis)
        self.thread.finished.connect(self.analyzer.deleteLater)
        self.thread.start()
        self.video.videoSink().videoFrameChanged.connect(self.on_frame)
        self.player.positionChanged.connect(self.position_changed)
        self.player.durationChanged.connect(self.duration_changed)
        self.player.playbackStateChanged.connect(self.state_changed)
        self.player.mediaStatusChanged.connect(self.media_status_changed)
        self.player.errorOccurred.connect(lambda error, message: self.log(f'Playback error: {message}'))
        self.devices.audioOutputsChanged.connect(self.refresh_outputs)
        self.refresh_outputs()
        self.log('Ready. Direction indicators preview visible face positions only; audio uses one output.')
        if self.settings['movie_path']:
            self.open_movie(Path(self.settings['movie_path']))

    def build_ui(self):
        self.setStyleSheet('''
            QMainWindow, QWidget { background: #101723; color: #e7edf5; font-size: 13px; }
            QLabel#heading { font-size: 24px; font-weight: 700; color: #67dfc1; }
            QGroupBox { border: 1px solid #334155; border-radius: 8px; margin-top: 12px; padding: 12px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; }
            QPushButton, QComboBox { background: #243247; padding: 9px; border: 1px solid #40536c; border-radius: 5px; }
            QPushButton:hover { background: #35506b; }
            QPushButton:disabled { color: #758397; background: #182231; }
            QPlainTextEdit { background: #0b111c; border: 1px solid #334155; font-family: Consolas; font-size: 12px; }
            QProgressBar { border: 0; background: #243247; height: 7px; color: transparent; }
            QProgressBar::chunk { background: #50d9b4; }
            QTabWidget::pane { border: 1px solid #334155; }
            QTabBar::tab { background: #182231; padding: 12px 24px; color: #aebcd0; }
            QTabBar::tab:selected { background: #243247; color: #67dfc1; }
        ''')
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.audio_theater_tab = QWidget()
        self.tabs.addTab(self.audio_theater_tab, 'Audio Theater')
        self.light_sound_tab = QWidget()
        self.tabs.addTab(self.light_sound_tab, 'Ligh And Sound')
        light_layout = QVBoxLayout(self.light_sound_tab)
        light_title = QLabel('Ligh And Sound')
        light_title.setObjectName('heading')
        light_layout.addWidget(light_title)
        light_layout.addWidget(QLabel('Light and sound controls will be added here.'))
        light_layout.addStretch()
        layout = QVBoxLayout(self.audio_theater_tab)
        title = QLabel('LIGHT & SOUND  /  THEATER EDGE')
        title.setObjectName('heading')
        layout.addWidget(title)
        layout.addWidget(QLabel('Movie playback · scene position analysis · spatial audio research'))
        header = QHBoxLayout()
        browse = QPushButton('Browse MP4…')
        browse.clicked.connect(self.browse)
        self.file_label = QLabel('Choose a movie to begin')
        self.file_label.setWordWrap(True)
        header.addWidget(browse)
        header.addWidget(self.file_label, 1)
        layout.addLayout(header)
        splitter = QSplitter(Qt.Horizontal)
        stage = QGroupBox('SCREEN POSITION PREVIEW — audio routing is not active')
        grid = QGridLayout(stage)
        self.indicators = {}
        places = {'top-left': (0, 0), 'top': (0, 1), 'top-right': (0, 2),
                  'left': (1, 0), 'right': (1, 2), 'bottom-left': (2, 0),
                  'bottom': (2, 1), 'bottom-right': (2, 2)}
        for direction, (row, col) in places.items():
            box = QWidget()
            box_layout = QVBoxLayout(box)
            label = QLabel(direction.upper())
            label.setAlignment(Qt.AlignCenter)
            meter = QProgressBar()
            meter.setRange(0, 100)
            meter.setValue(0)
            meter.setTextVisible(False)
            box_layout.addWidget(label)
            box_layout.addWidget(meter)
            grid.addWidget(box, row, col)
            self.indicators[direction] = meter
        self.video = QVideoWidget()
        self.video.setMinimumSize(480, 270)
        grid.addWidget(self.video, 1, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(1, 1)
        splitter.addWidget(stage)
        analysis = QGroupBox('EXTRACTED FRAME')
        side = QVBoxLayout(analysis)
        self.analysis_toggle = QCheckBox('Analyze visible face positions')
        self.analysis_toggle.setChecked(self.settings['analysis_enabled'])
        self.analysis_toggle.toggled.connect(self.toggle_analysis)
        side.addWidget(self.analysis_toggle)
        self.frame_preview = QLabel('Sampled frames appear here during playback')
        self.frame_preview.setAlignment(Qt.AlignCenter)
        self.frame_preview.setWordWrap(True)
        self.frame_preview.setMinimumSize(270, 180)
        side.addWidget(self.frame_preview, 1)
        self.analysis_status = QLabel('No frame analyzed yet')
        self.analysis_status.setWordWrap(True)
        side.addWidget(self.analysis_status)
        note = QLabel('Initial detector: frontal faces.\nNo speaker identification or car detection yet.\nScreen position does not establish room depth.\nOriginal audio plays on the selected output.')
        note.setWordWrap(True)
        side.addWidget(note)
        splitter.addWidget(analysis)
        splitter.setStretchFactor(0, 4)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)
        timeline = QHBoxLayout()
        self.time_label = QLabel('00:00:00 / 00:00:00')
        self.seek = QSlider(Qt.Horizontal)
        self.seek.setRange(0, 0)
        self.seek.setSingleStep(1000)
        self.seek.setPageStep(10000)
        self.seek.actionTriggered.connect(self.seek_action)
        self.seek.sliderReleased.connect(lambda: self.seek_to(self.seek.value()))
        timeline.addWidget(self.time_label)
        timeline.addWidget(self.seek, 1)
        layout.addLayout(timeline)
        controls = QHBoxLayout()
        self.transport = []
        for text, action in [('Play', self.player.play), ('Pause', self.player.pause),
                              ('Stop', self.stop_movie), ('Restart', self.restart_movie)]:
            button = QPushButton(text)
            button.clicked.connect(action)
            button.setEnabled(False)
            controls.addWidget(button)
            self.transport.append(button)
        self.playback_status = QLabel('Stopped')
        controls.addWidget(self.playback_status)
        controls.addStretch()
        controls.addWidget(QLabel('Volume'))
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setMaximumWidth(140)
        self.volume.setRange(0, 100)
        self.volume.setValue(self.settings['volume'])
        self.volume.valueChanged.connect(self.volume_changed)
        controls.addWidget(self.volume)
        layout.addLayout(controls)
        outputs = QHBoxLayout()
        outputs.addWidget(QLabel('Movie audio output'))
        self.output_combo = QComboBox()
        self.output_combo.currentIndexChanged.connect(self.select_output)
        outputs.addWidget(self.output_combo, 1)
        layout.addLayout(outputs)
        layout.addWidget(QLabel('EVENT TERMINAL'))
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(600)
        self.log_view.setMaximumHeight(145)
        layout.addWidget(self.log_view)

    def log(self, message):
        line = f'[{time.strftime("%H:%M:%S")}] {message}'
        self.log_view.appendPlainText(line)
        print(line, flush=True)

    def persist(self):
        try:
            save_config(self.config_path, self.settings)
        except OSError as error:
            self.log(f'Cannot save configuration: {error}')

    def browse(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, 'Open movie', self.settings['movie_path'],
            'MP4 movies (*.mp4 *.m4v);;Video files (*.mkv *.avi *.mov);;All files (*)')
        if filename:
            self.open_movie(Path(filename))

    def invalidate(self):
        self.epoch += 1
        self.last_sample = 0.
        for meter in self.indicators.values():
            meter.setValue(0)
        self.frame_preview.clear()
        self.frame_preview.setText('Waiting for a decoded frame')
        self.analysis_status.setText('No current scene analysis')

    def open_movie(self, path):
        path = Path(path).resolve()
        if not path.is_file():
            self.log(f'Movie not found: {path}. Browse to select another file.')
            return False
        self.player.stop()
        self.invalidate()
        self.player.setSource(QUrl.fromLocalFile(str(path)))
        self.settings['movie_path'] = str(path)
        self.persist()
        self.file_label.setText(path.name)
        self.file_label.setToolTip(str(path))
        for button in self.transport:
            button.setEnabled(True)
        self.log(f'Loaded: {path}')
        return True

    def seek_to(self, milliseconds):
        self.invalidate()
        self.player.setPosition(milliseconds)
        self.log(f'Seek: {clock(milliseconds)}')

    def seek_action(self, action):
        # actionTriggered precedes valueChanged; sliderPosition is already updated.
        if not self.seek.isSliderDown():
            self.seek_to(self.seek.sliderPosition())

    def stop_movie(self):
        self.player.stop()
        self.invalidate()

    def restart_movie(self):
        self.seek_to(0)
        self.player.play()

    def position_changed(self, position):
        if not self.seek.isSliderDown():
            self.seek.setValue(position)
        self.time_label.setText(f'{clock(position)} / {clock(self.player.duration())}')

    def duration_changed(self, duration):
        self.seek.setRange(0, duration)
        self.position_changed(self.player.position())

    def state_changed(self, state):
        label = {QMediaPlayer.PlayingState: 'Playing', QMediaPlayer.PausedState: 'Paused',
                 QMediaPlayer.StoppedState: 'Stopped'}[state]
        self.playback_status.setText(label)
        self.log(label)

    def media_status_changed(self, status):
        if status in (QMediaPlayer.EndOfMedia, QMediaPlayer.InvalidMedia):
            self.invalidate()

    def volume_changed(self, value):
        self.audio.setVolume(value / 100)
        self.settings['volume'] = value
        self.persist()

    def toggle_analysis(self, enabled):
        self.settings['analysis_enabled'] = enabled
        self.invalidate()
        self.persist()
        self.log(f'Scene analysis {"enabled" if enabled else "disabled"}')

    def refresh_outputs(self):
        self.output_combo.blockSignals(True)
        self.output_combo.clear()
        self.output_combo.addItem('System default', None)
        selected = 0
        for device in QMediaDevices.audioOutputs():
            self.output_combo.addItem(device.description(), device)
            if bytes(device.id()).hex() == self.settings['audio_device_id']:
                selected = self.output_combo.count() - 1
        self.output_combo.setCurrentIndex(selected)
        self.output_combo.blockSignals(False)
        device = self.output_combo.currentData()
        self.audio.setDevice(device if device else QMediaDevices.defaultAudioOutput())

    def select_output(self, index):
        device = self.output_combo.itemData(index)
        self.audio.setDevice(device if device else QMediaDevices.defaultAudioOutput())
        self.settings['audio_device_id'] = bytes(device.id()).hex() if device else ''
        self.persist()
        self.log(f'Audio output: {self.output_combo.currentText()}')

    def on_frame(self, frame):
        now = time.monotonic()
        if (self.busy or not self.analysis_toggle.isChecked() or not frame.isValid()
                or self.player.playbackState() != QMediaPlayer.PlayingState
                or now - self.last_sample < self.settings['sample_interval_ms'] / 1000):
            return
        image = frame.toImage()
        if image.isNull():
            return
        image = image.scaled(640, 400, Qt.KeepAspectRatio, Qt.SmoothTransformation).copy()
        self.last_sample = now
        self.busy = True
        self.analyze_frame.emit(dict(image=image, epoch=self.epoch,
                                    timestamp=self.player.position()))

    def accept_analysis(self, result):
        self.busy = False
        if result['epoch'] != self.epoch or not self.analysis_toggle.isChecked():
            return
        if result['error']:
            self.log(f'Analysis error: {result["error"]}')
            return
        self.analyzed_frames += 1
        image = result['image']
        if image is not None:
            self.frame_preview.setPixmap(QPixmap.fromImage(image).scaled(
                self.frame_preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))
        detections = result['detections']
        count = len(detections)
        gains = dict.fromkeys(DIRECTIONS, 0.)
        for detection in detections:
            for direction, gain in preview_gains(detection['x'], detection['y']).items():
                gains[direction] += gain * gain / count
        for direction, power in gains.items():
            self.indicators[direction].setValue(round(math.sqrt(power) * 100))
        positions = ', '.join(f'face {i}: {d["position"]}' for i, d in enumerate(detections, 1))
        message = positions or 'no frontal face detected; sound source unknown'
        self.analysis_status.setText(f'Frame {self.analyzed_frames} · {clock(result["timestamp"])}\n{message}')
        self.log(f'Movie {clock(result["timestamp"])} | {message}')

    def closeEvent(self, event):
        self.player.stop()
        # Stopping retains the decoder/source and its Windows file handle.
        self.player.setSource(QUrl())
        self.invalidate()
        self.thread.quit()
        self.thread.wait()
        self.persist()
        event.accept()

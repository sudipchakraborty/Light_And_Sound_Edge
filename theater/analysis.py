"""Bounded, CPU-only initial face-position analysis of decoded movie frames."""
import cv2
import numpy as np
from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtGui import QImage
from .spatial import screen_position


class FrameAnalyzer(QObject):
    completed = Signal(object)

    def __init__(self):
        super().__init__()
        self.detector = None

    @Slot(object)
    def analyze(self, job):
        result = dict(epoch=job['epoch'], timestamp=job['timestamp'],
                      detections=[], image=None, error='')
        try:
            if self.detector is None:
                self.detector = cv2.CascadeClassifier(
                    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                if self.detector.empty():
                    raise RuntimeError('Face detection model could not be loaded')
            image = job['image'].convertToFormat(QImage.Format_RGB888)
            rows = np.frombuffer(image.constBits(), dtype=np.uint8).reshape(
                image.height(), image.bytesPerLine())
            rgb = rows[:, :image.width() * 3].reshape(image.height(), image.width(), 3).copy()
            gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
            faces = self.detector.detectMultiScale(gray, scaleFactor=1.15,
                                                   minNeighbors=5, minSize=(24, 24))
            for number, (x, y, w, h) in enumerate(sorted(faces, key=lambda b: -b[2] * b[3]), 1):
                cx, cy = (x + w / 2) / image.width(), (y + h / 2) / image.height()
                position = screen_position(cx, cy)
                result['detections'].append(dict(x=cx, y=cy, position=position))
                cv2.rectangle(rgb, (x, y), (x + w, y + h), (50, 220, 180), 2)
                cv2.putText(rgb, f'Face {number}: {position}', (x, max(16, y - 8)),
                            cv2.FONT_HERSHEY_SIMPLEX, .45, (50, 220, 180), 1)
            result['image'] = QImage(rgb.data, image.width(), image.height(),
                                     rgb.strides[0], QImage.Format_RGB888).copy()
        except Exception as error:
            result['error'] = str(error)
        self.completed.emit(result)

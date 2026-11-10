import sys
from PySide6.QtWidgets import QApplication
from theater.app import TheaterWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('Light & Sound Theater Edge')
    window = TheaterWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())

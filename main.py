# main.py
import sys
import signal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer
from ui_main import MainWindow
from database import init_db

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")

    # Permet à Python de traiter ses signaux même dans la boucle Qt
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    timer = QTimer()
    timer.start(200)
    timer.timeout.connect(lambda: None)

    init_db()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
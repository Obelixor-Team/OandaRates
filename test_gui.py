import sys
from PyQt6.QtWidgets import QApplication, QWidget

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Test PyQt6 GUI")
    window.setGeometry(100, 100, 400, 300)
    window.show()
    sys.exit(app.exec())
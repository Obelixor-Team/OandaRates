import sys
from PyQt6.QtWidgets import QApplication, QWidget, QLabel

def main():
    app = QApplication(sys.argv)
    window = QWidget()
    window.setWindowTitle("Minimal PyQt6 GUI")
    QLabel("Hello, PyQt6!", parent=window)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()

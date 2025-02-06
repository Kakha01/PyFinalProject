import sys
from PyQt6.QtWidgets import QApplication
from gui import MainWindow
from db.functions import create_all


if __name__ == "__main__":
    create_all()
    app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec()

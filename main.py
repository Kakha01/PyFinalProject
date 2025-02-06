import sys, logging
from PyQt6.QtWidgets import QApplication
from gui import MainWindow
from db.functions import create_all

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


if __name__ == "__main__":
    create_all()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = MainWindow()
    w.show()
    app.exec()

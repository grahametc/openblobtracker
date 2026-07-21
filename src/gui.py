import sys, os
import cv2 as cv
import blobtracker
from threading import Thread

from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QDial,
    QDoubleSpinBox,
    QFontComboBox,
    QLabel,
    QLCDNumber,
    QLineEdit,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QSlider,
    QSpinBox,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
    QFileDialog
)


# Subclass QMainWindow to customize your application's main window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("My App")
        layout = QVBoxLayout()
        self.setFixedSize(QSize(400, 600))
        #
        self.button = QPushButton("Select File")
        self.button.setFixedSize(400, 100)
        self.setCentralWidget(self.button)
        #
        thresh_slider = QSlider()
        thresh_slider.setMinimum(0)
        thresh_slider.setMaximum(100)
        thresh_slider.setSingleStep(1)
        #
        layout.addWidget(self.button)
        layout.addWidget(thresh_slider)
        path = self.button.clicked.connect(self.select_file)
        if path:
            print(path)

    def select_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select File", "", "Video Files (*.mp4 *.mov)")
        if path:
            self.selected_path = path
            self.button.hide()
            print(path)
            blobtracker.main(path, 0, 2147483647, (255,255,255), 1, 0, (255,255,255), True, (255,255,255), 200, False, (255,255,255), False, False, (10, 10), 2147483647)
        return path    


         

app = QApplication(sys.argv)

window = MainWindow()
window.show()

app.exec()
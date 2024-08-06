from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QHBoxLayout
import pyqtgraph as pg
from pypylon import pylon
from pyqtgraph.Qt import QtCore
import numpy as np
import time
from ImageHandler import ImageHandler


# Make a simple widget
class AutofocusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Autofocus App")
        self.initialise_button = QPushButton("Initialise camera")
        self.load_config_button = QPushButton("Load configuration")

        self.monitor_button = QPushButton("Monitor")
        self.lock_button = QPushButton("Lock")

        self.show_camera_feed_button = QPushButton("Show camera feed")

        self.plot_canvas = pg.PlotWidget(background=None)

        self.layout = QVBoxLayout()
        # add to layout
        self.layout.addWidget(self.initialise_button)
        self.layout.addWidget(self.load_config_button)
        self.button_group = QHBoxLayout()
        self.button_group.addWidget(self.monitor_button)
        self.button_group.addWidget(self.lock_button)
        self.layout.addLayout(self.button_group)
        self.layout.addWidget(self.plot_canvas)
        self.layout.addWidget(self.show_camera_feed_button)

        self.setLayout(self.layout)

        self.initialise_button.clicked.connect(self._on_initialise_button_clicked)
        self.monitor_button.clicked.connect(self._on_monitor_button_clicked)
        self.lock_button.clicked.connect(self._on_lock_button_clicked)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

        self.curve = self.plot_canvas.plot(pen='y')
        self.data = []
        self.time = []
        self.ptr = 0

    def _on_initialise_button_clicked(self):
        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()
        self.camera.PixelFormat.SetValue('Mono8')
        self.exposure_time_ms = 100
        self.camera.ExposureTime.SetValue(self.exposure_time_ms * 1000)
        print("Camera initialised!")

    def _on_lock_button_clicked(self):
        i = 0

        while self.camera.IsGrabbing():
            grab = self.camera.RetrieveResult(150)
            print(grab.GrabSucceeded())

    def _on_monitor_button_clicked(self):
        # self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
        # instantiate callback handler
        self.CameraHandler = ImageHandler(self.camera)
        # register with the pylon loop
        self.camera.RegisterImageEventHandler(self.CameraHandler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)
        # fetch some images with background loop
        self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
        print('Free-run acquisition started!')


        self.timer.start(100)



    def update(self):
        # grab = self.camera.RetrieveResult(150)
        # img = grab.GetArray()


        self.data.append(self.CameraHandler.img.mean())
        self.time.append(self.ptr)

        # self.curve.setData(self.data[self.ptr%2])
        self.curve.setData(self.time, self.data)

        self.plot_canvas.enableAutoRange('xy', True)
        self.ptr += 1




if __name__ == "__main__":
    app = QApplication([])
    widget = AutofocusApp()
    widget.show()
    app.exec()

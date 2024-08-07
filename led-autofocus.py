from qtpy.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QSlider, QHBoxLayout, QGridLayout
import pyqtgraph as pg
from pypylon import pylon
from pyqtgraph.Qt import QtCore
import numpy as np
import time
from ImageHandler import ImageHandler


#TODO: Ensure camera feed opens up a separate window
#TODO: Fix aspect ratio of the focus position plot window
#TODO: Implement connection to the pymm-core


# enable emulation
import os
os.environ["PYLON_CAMEMU"] = "1"

# Make a simple widget
class AutofocusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 600, 500)
        self.setWindowTitle("Autofocus App")
        self.initialise_button = QPushButton("Initialise camera")
        self.load_config_button = QPushButton("Load configuration")

        self.monitor_button = QPushButton("Monitor")
        self.lock_button = QPushButton("Lock")

        self.show_camera_feed_button = QPushButton("Show camera feed")

        self.plot_canvas = pg.PlotWidget(background=None)
        self.video_view = pg.PlotWidget(background=None, visible=False)
        # self.video_view = pg.GraphicsView()
        self.video_canvas = pg.ImageItem()
        self.video_view.hideAxis('left')
        self.video_view.hideAxis('bottom')
        self.video_view.setMouseEnabled(x=False, y=False)
        self.video_view.addItem(self.video_canvas)

        self.x_canvas = pg.PlotWidget()
        self.y_canvas = pg.PlotWidget()

        self.layout = QGridLayout()
        # add to layout
        self.layout.addWidget(self.initialise_button, 0, 0)
        self.layout.addWidget(self.load_config_button, 0, 1)
        self.button_group = QHBoxLayout()
        self.button_group.addWidget(self.monitor_button)
        self.button_group.addWidget(self.lock_button)
        self.layout.addLayout(self.button_group, 1, 0, 1, 2)
        self.layout.addWidget(self.plot_canvas, 2, 0, 4, 2)
        self.layout.addWidget(self.show_camera_feed_button, 6, 0, 1, 2)

        # self.grid_layout = QGridLayout()
        # self.grid_layout.addWidget(self.video_view, 0, 0, 2, 1)
        # self.grid_layout.addWidget(self.x_canvas, 0, 1, 1, 1)
        # self.grid_layout.addWidget(self.y_canvas, 1, 1, 1, 1)
        # self.layout.addLayout(self.grid_layout, 7, 0, 2, 2)

        self.setLayout(self.layout)

        self.initialise_button.clicked.connect(self._on_initialise_button_clicked)
        self.monitor_button.clicked.connect(self._on_monitor_button_clicked)
        self.lock_button.clicked.connect(self._on_lock_button_clicked)

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

        self.curve = self.plot_canvas.plot(pen='y')
        self.x_plot = self.x_canvas.plot(pen='r')
        self.y_plot = self.y_canvas.plot(pen='r')

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
        self.video_view.resize(self.camera.Width.Value/4, self.camera.Height.Value/4)
        # self.video_view.setYRange((0, self.camera.Height.Value))
        # self.video_view.setXRange((0, self.camera.Width.Value))
        self.video_view.setAspectLocked(True)
        print(self.camera.Height.Value)
        print(self.camera.Width.Value)


    def _on_lock_button_clicked(self):
        # to be written.
        pass
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
        img = self.CameraHandler.img

        # calculate projection over columns
        x_projection = img.mean(axis=0)
        y_projection = img.mean(axis=1)

        # add random integer to the data
        img = img + np.random.randint(0, 255, img.shape)

        self.data.append(img.mean())
        self.time.append(self.ptr)

        # self.curve.setData(self.data[self.ptr%2])
        self.curve.setData(self.time, self.data)
        self.x_plot.setData(x_projection)
        self.y_plot.setData(y_projection)

        # self.plot_canvas.enableAutoRange('xy', True)
        # self.x_canvas.enableAutoRange('xy', True)
        # self.y_canvas.enableAutoRange('xy', True)

        self.video_canvas.setImage(img)
        self.ptr += 1


def test_function():
    app = QApplication([])
    widget = AutofocusApp()
    widget.show()
    app.exec()
    return widget


if __name__ == "__main__":
    test_function()

from qtpy.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                            QLabel, QLineEdit, QHBoxLayout, QGridLayout)
import pyqtgraph as pg
from pypylon import pylon
from pyqtgraph.Qt import QtCore
import numpy as np
import json
from qtpy.QtCore import Qt
from pymmcore_plus import CMMCorePlus
from .ImageHandler import ImageHandler
from .fit_testing import fit_gaussian, Gaussian1D
from pathlib import Path
from napari.qt.threading import thread_worker
from .settings_panel import SettingsPanel

testing = False

if testing:
    # enable emulation
    import os
    os.environ["PYLON_CAMEMU"] = "1"

class AutofocusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 850, 700)
        self.setWindowTitle("Autofocus App")

        # PYMMCORE
        self.mmc = CMMCorePlus.instance()

        # BUTTONS
        self.camera_settings_button = QPushButton("Camera settings")
        self.initialise_button = QPushButton("Initialise plugin")
        self.monitor_button = QPushButton("Monitor")
        self.lock_button = QPushButton("Definitely focus?")
        self.lock_button.setStyleSheet("font: italic;")
        self.show_camera_feed_button = QPushButton("Show camera feed")
        self.close_camera = QPushButton("Close camera (requires re-initialisation)")

        # Lock and monitor buttons need to be checkable
        self.lock_button.setCheckable(True)
        self.monitor_button.setCheckable(True)
        self.show_camera_feed_button.setCheckable(True)

        # Plot widget for focus position
        self.plot_canvas = pg.PlotWidget(background=None)
        self.plot_canvas.setMinimumHeight(200)

        # Video widget for camera feed and projections
        self.video_view = pg.PlotWidget(background=None, visible=False)
        self.video_canvas = pg.ImageItem()
        self.video_view.hideAxis('left')
        self.video_view.hideAxis('bottom')
        self.video_view.setMouseEnabled(x=False, y=False)
        self.video_view.addItem(self.video_canvas)

        self.x_canvas = pg.PlotWidget(background=None)
        self.y_canvas = pg.PlotWidget(background=None)

        # LAYOUT
        self.layout = QGridLayout()


        button_group = QHBoxLayout()
        button_group.addWidget(self.camera_settings_button)
        button_group.addWidget(self.initialise_button)
        button_group.addWidget(self.close_camera)
        self.layout.addLayout(button_group, 0, 0, 1, 2)

        self.button_group = QHBoxLayout()
        self.button_group.addWidget(self.monitor_button)
        self.button_group.addWidget(self.lock_button)
        self.layout.addLayout(self.button_group, 1, 0, 1, 2)
        self.layout.addWidget(self.plot_canvas, 2, 0, 4, 2)

        self.layout.addWidget(self.show_camera_feed_button, 6, 0, 1, 2)

        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(self.video_view, 0, 0, 2, 1)
        self.grid_layout.addWidget(self.x_canvas, 0, 1, 1, 1)
        self.grid_layout.addWidget(self.y_canvas, 1, 1, 1, 1)
        self.layout.addLayout(self.grid_layout, 7, 0, 2, 2)

        self.setLayout(self.layout)

        # TIMER
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)

        # PLOT
        self.monitor_curve = self.plot_canvas.plot(pen='y')
        self.locked_position = 0
        self.locked_position_curve = self.plot_canvas.plot(pen=pg.mkPen('r', style=Qt.DashLine))

        self.x_plot = self.x_canvas.plot(pen='r')
        self.x_fit_plot = self.x_canvas.plot(pen=pg.mkPen('y', style=Qt.DashLine))
        self.y_plot = self.y_canvas.plot(pen='r')
        self.y_fit_plot = self.y_canvas.plot(pen=pg.mkPen('y', style=Qt.DashLine))

        # DATA STORAGE
        self.data = []
        self.time = []
        self.ptr = 0

        # CONNECT ACTIONS
        self.camera_settings_button.clicked.connect(self._on_camera_settings_button_clicked)
        self.initialise_button.clicked.connect(self._on_initialise_button_clicked)
        self.monitor_button.clicked.connect(self._on_monitor_button_clicked)
        self.lock_button.clicked.connect(self._on_lock_button_clicked)
        self.show_camera_feed_button.clicked.connect(self._on_show_camera_feed_button_clicked)
        self.close_camera.clicked.connect(self._on_close_camera_button_clicked)

        self.value = 0

    def _on_close_camera_button_clicked(self):
        if hasattr(self, "camera"):
            self.camera.Close()
            print("Camera closed!")
        else:
            print("No camera to close!")

    def _on_camera_settings_button_clicked(self):
        self.settings_panel = SettingsPanel()
        self.settings_panel.show()

    def _on_initialise_button_clicked(self):
        # GUESS VALUES - will be constantly updated
        self.guessx = [0, 2000, 300, 20000]
        self.guessy = [0, 800, 300, 20000]
        self.current_z = 0
        self.last_movement = 0

        # Check if the camera is already initialised
        if hasattr(self, "camera"):
            self.camera.Close()

        # LOAD SETTINGS
        config_path = Path(__file__).parent / "autofocus_config.json"
        with open(config_path, "r") as f:
            self.settings = json.load(f)

        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()

        #TODO: move these parameters to the .json file

        if testing:
            self.camera.TestImageSelector.Value = "Off"
            # Enable custom test images
            self.camera.ImageFileMode.Value = "On"
            # Load custom test image from disk
            self.camera.ImageFilename.Value = 'C:\\Users\\u1870329\\Documents\\GitHub\\microscope-control\\test-data\\'

        # Set camera parameters
        self.camera.Width.Value = self.settings["width"]
        self.camera.Height.Value = self.settings["height"]
        self.camera.OffsetX.Value = self.settings["offset_x"]
        self.camera.OffsetY.Value = self.settings["offset_y"]
        self.camera.PixelFormat.SetValue('Mono8')
        self.camera.Gain.SetValue(self.settings["gain"])
        self.exposure_time_ms = self.settings["exposure_time_ms"]
        self.camera.ExposureTime.SetValue(self.exposure_time_ms * 1000)
        print("Camera initialised!")
        self.video_view.resize(np.ceil(self.camera.Width.Value/4), np.ceil(self.camera.Height.Value/4))
        self.video_view.setAspectLocked(True)

        # z-movement parameters
        self.max_movement = self.settings["max_movement"]


        # instantiate callback handler
        self.CameraHandler = ImageHandler(self.camera)
        # register with the pylon loop
        self.camera.RegisterImageEventHandler(self.CameraHandler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)

    def _on_lock_button_clicked(self):
        if self.lock_button.isChecked():
            # make sure camera starts grabbing
            if not self.camera.IsGrabbing():
                self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
                print('Free-run acquisition started!')

            self.get_lock_position()
            self.lock_button.setText("Definitely focused!")
            self.lock_button.setStyleSheet("font: italic bold; color: white; background-color: green;")
        elif not self.lock_button.isChecked():
            self.lock_button.setStyleSheet("font: italic;")
            self.lock_button.setText("Definitely focus?")
            if self.camera.IsGrabbing() and not self.monitor_button.isChecked() and not self.show_camera_feed_button.isChecked():
                self.camera.StopGrabbing()
                print('Free-run acquisition stopped!')
        pass

    def _on_monitor_button_clicked(self):
        if self.monitor_button.isChecked():
            self.ptr = 0
            # Check if the camera is grabbing or the timer is active (i.e. if the lock is already engaged)
            if self.camera.IsGrabbing():
                pass
            else:
                self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
                print('Free-run acquisition started!')
            if not self.timer.isActive():
                self.timer.start(1*self.camera.ExposureTime.Value/1000)

            # Clear the graph whenever monitor is restarted
            self.data = []
            self.time = []
        if not self.monitor_button.isChecked() and not self.lock_button.isChecked() and not self.show_camera_feed_button.isChecked():
            self.camera.StopGrabbing()
            print('Free-run acquisition stopped!')
            self.timer.stop()

    def _on_show_camera_feed_button_clicked(self):
        # start acquisition and timer if not already started
        if self.show_camera_feed_button.isChecked():
            if not self.camera.IsGrabbing():
                self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
                print('Free-run acquisition started!')
            if not self.timer.isActive():
                self.timer.start(self.camera.ExposureTime.Value/1000)
        pass

    def update_plots_and_position(self):
        # update plots
        if self.show_camera_feed_button.isChecked():
            self.video_canvas.setImage(self.CameraHandler.img)
            self.x_plot.setData(self.CameraHandler.x_projection)
            self.y_plot.setData(self.CameraHandler.y_projection)
            if self.lock_button.isChecked() or self.monitor_button.isChecked():
                self.x_fit_plot.setData(
                    Gaussian1D(np.linspace(0, self.CameraHandler.x_projection.shape[0], self.CameraHandler.x_projection.shape[0]), *self.guessx))
                self.y_fit_plot.setData(
                    Gaussian1D(np.linspace(0, self.CameraHandler.y_projection.shape[0], self.CameraHandler.y_projection.shape[0]), *self.guessy))
            else:
                self.x_fit_plot.clear()
                self.y_fit_plot.clear()

        if self.monitor_button.isChecked():
            self.monitor_curve.setData(self.time, self.data)
            if self.lock_button.isChecked():
                self.locked_position_curve.setData(self.time, [(x * 0 + self.locked_position) for x in self.data])

        # update position
        if self.lock_button.isChecked():
            # calculate required movement
            self.required_movement = (self.locked_position - self.current_z) * 0.001  # movement is in um

            # TODO: set this to a json parameter
            if np.abs(self.required_movement) > self.max_movement:  # change back to 0.4
                print("Movement too big. No movement.")
                # Disengage the lock button
                self.lock_button.setChecked(False)
                self.lock_button.setStyleSheet("font: italic bold; color: white; background-color: red;")
                self.lock_button.setText("Definitely NOT focused!")

            else:
                # print(f"Required movement is {self.required_movement * 1000}")
                self.last_movement = self.required_movement
                if np.abs(self.required_movement)*1000 < 20:
                    self.mmc.setRelativeXYZPosition(0, 0, self.required_movement)

        # clear data if too large
        if len(self.time) > 100:
            self.time = []
            self.data = []
            self.ptr = 0

        self.ptr += 1
        return

    @thread_worker(connect={"returned": update_plots_and_position})
    def grab_images_on_thread(self):
        # this function should do the heavy lifting, as it is run in a separate thread
        # TODO: Should probably avoid creating new variables, will slow things down possibly?
        img = self.CameraHandler.img
        x_projection = self.CameraHandler.x_projection
        y_projection = self.CameraHandler.y_projection

        if self.lock_button.isChecked() or self.monitor_button.isChecked():
            self.guessx = fit_gaussian(np.linspace(0, x_projection.shape[0], x_projection.shape[0]), x_projection,
                                       self.guessx)
            self.guessy = fit_gaussian(np.linspace(0, y_projection.shape[0], y_projection.shape[0]), y_projection,
                                       self.guessy)



            polyfit = [self.settings["p2"], self.settings["p1"], self.settings["p0"]]

            self.current_z = -np.polyval(polyfit, self.guessx[2] - self.guessy[2])

            # print(f"Difference: {self.guessx[2] - self.guessy[2]}, Current Z: {self.current_z}")

            # get current position - this needs to be multiplied by the values from the fit
            # self.current_z = ((self.guessx[2]-self.guessy[2])**2 * self.settings["p2"]) + ((self.guessx[2] - self.guessy[2]) * self.settings["p1"])+ self.settings["p0"]

            # calculate required movement from the target position, with constraints in place

        if self.monitor_button.isChecked():
            self.data.append(self.current_z)
            self.time.append(self.ptr)
        return self

    def update(self):
        self.grab_images_on_thread()

    def get_lock_position(self):
        img = self.CameraHandler.img
        x_projection = self.CameraHandler.x_projection
        y_projection = self.CameraHandler.y_projection

        x_fit = fit_gaussian(np.linspace(0, x_projection.shape[0], x_projection.shape[0]), x_projection,
                                         self.guessx)
        y_fit = fit_gaussian(np.linspace(0, y_projection.shape[0], y_projection.shape[0]), y_projection,
                                         self.guessy)

        # Update guess values - makes next fit easier and faster
        self.guessx = x_fit
        self.guessy = y_fit

        polyfit = [self.settings["p2"], self.settings["p1"], self.settings["p0"]]
        self.locked_position = -np.polyval(polyfit, self.guessx[2] - self.guessy[2])
        return

def test_function():
    app = QApplication([])
    widget = AutofocusApp()

    # settings = {"exposure_time": 100, "gain": 1, "roi": [0, 0, 1528, 1528], "p1": 1, "p0": 0}
    #
    # widget = SettingsPanel(settings)
    widget.show()
    app.exec()
    return widget


if __name__ == "__main__":
    mmc = CMMCorePlus.instance()
    mmc.loadSystemConfiguration()  # load demo configuration
    test_function()

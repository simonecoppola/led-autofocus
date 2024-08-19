from qtpy.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                            QLabel, QLineEdit, QHBoxLayout, QGridLayout)
import pyqtgraph as pg
from pypylon import pylon
from pyqtgraph.Qt import QtCore
import numpy as np
import time
from ImageHandler import ImageHandler
import fit_testing
import json
from qtpy.QtCore import Qt
from pymmcore_plus import CMMCorePlus


#TODO: Implement connection to the pymm-core


# enable emulation
import os
os.environ["PYLON_CAMEMU"] = "1"


#TODO: implement lock function and logic
#TODO: implement config loading

# Make a simple widget
class AutofocusApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 850, 700)
        self.setWindowTitle("Autofocus App")

        # LOAD SETTINGS
        with open("autofocus_config.json", "r") as f:
            self.settings = json.load(f)

        # PYMMCORE
        self.mmc = None

        # BUTTONS
        self.initialise_button = QPushButton("Initialise camera")
        self.load_config_button = QPushButton("Load configuration")
        self.monitor_button = QPushButton("Monitor")
        self.lock_button = QPushButton("Definitely focus?")
        self.lock_button.setStyleSheet("font: italic;")
        self.show_camera_feed_button = QPushButton("Show camera feed")
        self.link_to_pymmcore_button = QPushButton("Link to PyMMCore")

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
        button_group.addWidget(self.initialise_button)
        button_group.addWidget(self.load_config_button)
        button_group.addWidget(self.link_to_pymmcore_button)
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

        # GUESS VALUES - will be constantly updated
        self.guessx = [0, 800, 300, 20000]
        self.guessy = [0, 800, 300, 20000]
        self.current_z = 0
        self.last_movement = 0

        # CONNECT ACTIONS
        self.initialise_button.clicked.connect(self._on_initialise_button_clicked)
        self.monitor_button.clicked.connect(self._on_monitor_button_clicked)
        self.lock_button.clicked.connect(self._on_lock_button_clicked)
        self.show_camera_feed_button.clicked.connect(self._on_show_camera_feed_button_clicked)


    def _on_link_to_pymmcore_button_clicked(self):
        self.mmc = CMMCorePlus.instance()


    def _on_initialise_button_clicked(self):
        # Print the status of the monitor and lock buttons
        print(f"Monitor button status: {self.monitor_button.isChecked()}")
        print(f"Lock button status: {self.lock_button.isChecked()}")

        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()

        # THIS IS ONLY WHEN USING FAKE CAMERA - WILL NEED TO BE DELETED
        self.camera.Width.Value = 1624
        self.camera.Height.Value = 1626
        self.camera.TestImageSelector.Value = "Off"
        # Enable custom test images
        self.camera.ImageFileMode.Value = "On"
        # Load custom test image from disk
        self.camera.ImageFilename.Value = 'C:\\Users\\u1870329\\Documents\\GitHub\\led-autofocus\\test-data\\'

        self.camera.PixelFormat.SetValue('Mono8')
        self.exposure_time_ms = self.settings["exposure_time_ms"]
        self.camera.ExposureTime.SetValue(self.exposure_time_ms * 1000)
        self.camera.Gain.SetValue(self.settings["gain"])
        print("Camera initialised!")
        self.video_view.resize(np.ceil(self.camera.Width.Value/4), np.ceil(self.camera.Height.Value/4))
        # self.video_view.setYRange((0, self.camera.Height.Value))
        # self.video_view.setXRange((0, self.camera.Width.Value))
        self.video_view.setAspectLocked(True)
        print(self.camera.Height.Value)
        print(self.camera.Width.Value)
        # instantiate callback handler
        self.CameraHandler = ImageHandler(self.camera)
        # register with the pylon loop
        self.camera.RegisterImageEventHandler(self.CameraHandler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)
        # fetch some images with background loop

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
        # self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
        if self.monitor_button.isChecked():
            # Check if the camera is grabbing or the timer is active (i.e. if the lock is already engaged)
            if self.camera.IsGrabbing():
                pass
            else:
                self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
                print('Free-run acquisition started!')
            if not self.timer.isActive():
                self.timer.start(self.camera.ExposureTime.Value/1000)

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

        # We don't stop those two if the button is unchecked, as we want to keep the camera feed running based on the other buttons.
        pass

    def update(self):
        # TODO: Should probably avoid creating new variables, will slow things down possibly?
        img = self.CameraHandler.img
        x_projection = self.CameraHandler.x_projection
        y_projection = self.CameraHandler.y_projection

        if self.lock_button.isChecked() or self.monitor_button.isChecked():
            # TODO: this should be a separate function which returns the current z position
            # TODO: another function should calculate required movement based on the current z position
            # TODO: make sure to include higher and lower boundaries for move!
            self.guessx = fit_testing.fit_gaussian(np.linspace(0, x_projection.shape[0], x_projection.shape[0]), x_projection, self.guessx)
            self.guessy = fit_testing.fit_gaussian(np.linspace(0, y_projection.shape[0], y_projection.shape[0]), y_projection, self.guessy)

            # get current position - this needs to be multiplied by the values from the fit
            self.current_z = (self.guessx[2] - self.guessy[2]) * self.settings["p1"]

            if self.lock_button.isChecked():
                # calculate required movement
                self.required_movement = self.locked_position - self.current_z
                # move stage
                # TODO: left intentionally empty as this is the connection with pymmcore

            # calculate required movement from the target position, with constraints in place

        if self.monitor_button.isChecked():
            self.data.append(self.current_z)
            self.time.append(self.ptr)

        # update plots
        if self.show_camera_feed_button.isChecked():
            self.video_canvas.setImage(img)
            self.x_plot.setData(x_projection)
            self.y_plot.setData(y_projection)
            if self.lock_button.isChecked() or self.monitor_button.isChecked():
                self.x_fit_plot.setData(
                    fit_testing.Gaussian1D(np.linspace(0, x_projection.shape[0], x_projection.shape[0]), *self.guessx))
                self.y_fit_plot.setData(
                    fit_testing.Gaussian1D(np.linspace(0, y_projection.shape[0], y_projection.shape[0]), *self.guessy))
            else:
                self.x_fit_plot.clear()
                self.y_fit_plot.clear()

        if self.monitor_button.isChecked():
            self.monitor_curve.setData(self.time, self.data)
            if self.lock_button.isChecked():
                self.locked_position_curve.setData(self.time, [(x*0+self.locked_position) for x in self.data])



        self.ptr += 1

    def get_lock_position(self):
        img = self.CameraHandler.img
        x_projection = self.CameraHandler.x_projection
        y_projection = self.CameraHandler.y_projection

        x_fit = fit_testing.fit_gaussian(np.linspace(0, x_projection.shape[0], x_projection.shape[0]), x_projection,
                                         self.guessx)
        y_fit = fit_testing.fit_gaussian(np.linspace(0, y_projection.shape[0], y_projection.shape[0]), y_projection,
                                         self.guessy)

        # Update guess values - makes next fit easier and faster
        self.guessx = x_fit
        self.guessy = y_fit

        self.locked_position = (x_fit[2] - y_fit[2])*self.settings["p1"]
        return


class SettingsPanel(QWidget):
    def __init__(self, current_settings=None):
        super().__init__()
        # Set window title
        self.setWindowTitle("LED Autofocus Settings")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        if current_settings is not None:
            self.exposure_time = InputLine("Exposure time (ms)", current_settings["exposure_time"])
            self.gain = InputLine("Gain", current_settings["gain"])
            self.roi = InputLine("ROI [x y w h]", current_settings["roi"])
            self.p1 = InputLine("p1", current_settings["p1"])
            self.p2 = InputLine("p0", current_settings["p0"])
        else:
            self.exposure_time = InputLine("Exposure time (ms)")
            self.gain = InputLine("Gain")
            self.roi = InputLine("ROI [x y w h]")
            self.p1 = InputLine("p1")
            self.p2 = InputLine("p0")

        # self.exposure_time = InputLine("Exposure time (ms)")
        # self.gain = InputLine("Gain")
        # self.roi = InputLine("ROI [x y w h]")
        # self.p1 = InputLine("p1")
        # self.p2 = InputLine("p0")

        self.camera_settings_label = QLabel("Camera settings")
        self.camera_settings_label.setStyleSheet("font: bold; font-size: 16px;")
        self.calibration_settings_label = QLabel("Calibration settings")
        self.calibration_settings_label.setStyleSheet("font: bold; font-size: 16px;")
        self.calibration_settings_hint = QLabel("Calibration line is y = p1*x + p0")
        self.calibration_settings_hint.setContentsMargins(0, 0, 0, 0)

        self.update_settings_button = QPushButton("Update settings")
        self.update_settings_button.setMinimumHeight(50)

        self.layout.addWidget(self.camera_settings_label)
        self.layout.addWidget(self.exposure_time)
        self.layout.addWidget(self.gain)
        self.layout.addWidget(self.roi)
        self.layout.addWidget(self.calibration_settings_label)
        self.layout.addWidget(self.calibration_settings_hint)
        self.layout.addWidget(self.p1)
        self.layout.addWidget(self.p2)
        self.layout.addWidget(self.update_settings_button)



class InputLine(QWidget):
    def __init__(self, labelname="Input", initial_value=""):
        super().__init__()

        # Check if initial value is a number
        if type(initial_value) == int or type(initial_value) == float:
            initial_value = str(initial_value)
        elif type(initial_value) == list:
            initial_value = f"{initial_value[0]} {initial_value[1]} {initial_value[2]} {initial_value[3]}"


        self.label = QLabel(labelname)
        self.input = QLineEdit(initial_value)
        self.input.setMinimumSize(100, 25)
        self.input.setMaximumSize(100, 25)

        self.layout = QHBoxLayout()
        self.setLayout(self.layout)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input)

        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setContentsMargins(0, 0, 0, 0)

        self.input.textChanged.connect(self._on_text_changed)

    def _on_text_changed(self):
        print(f"Text changed to {self.input.text()}")



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

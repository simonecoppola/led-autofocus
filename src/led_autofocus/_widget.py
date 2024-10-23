import time

from qtpy.QtWidgets import (QApplication, QWidget, QPushButton, QHBoxLayout, QGridLayout, QSizePolicy)
import pyqtgraph as pg
from pypylon import pylon
from pyqtgraph.Qt import QtCore
import numpy as np
import json
from qtpy.QtCore import Qt
from pymmcore_plus import CMMCorePlus
from .ImageHandler import ImageHandler
from pathlib import Path
from ._settings_widget import SettingsPanel


class AutofocusWidget(QWidget):
    def __init__(self, mmc: CMMCorePlus = CMMCorePlus.instance()):
        super().__init__()
        # PYMMCORE
        self.mmc = mmc

        # WINDOW SETTINGS
        self.setMaximumHeight(550)
        self.setMaximumWidth(550)
        self.max_size = [550, 550]
        self.setGeometry(100, 100, 550, 350)
        self.min_size = self.size()
        print(self.min_size)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.MinimumExpanding)
        self.setWindowTitle("Autofocus App")

        # BUTTONS
        self.camera_settings_button = QPushButton("Camera settings")
        self.initialise_button = QPushButton("Initialise plugin")
        self.monitor_button = QPushButton("Monitor")
        self.lock_button = QPushButton("Definitely focus?")
        self.lock_button.setStyleSheet("font: italic;")
        self.recall_focus_button = QPushButton("Recall Focus")
        self.recall_focus_button.setCheckable(True)
        self.show_camera_feed_button = QPushButton("Show camera feed")
        self.close_camera = QPushButton("Close camera")
        self.recall_surface_btn = QPushButton("Recall Surface")

        # Lock and monitor buttons need to be checkable
        self.lock_button.setCheckable(True)
        self.monitor_button.setCheckable(True)
        self.show_camera_feed_button.setCheckable(True)

        # Plot widget for focus position
        self.plot_canvas = pg.PlotWidget(background=None)
        self.plot_canvas.setMinimumHeight(200)
        self.plot_canvas.setMaximumHeight(200)

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
        self.button_group.addWidget(self.recall_focus_button)
        self.button_group.addWidget(self.recall_surface_btn)
        self.layout.addWidget(self.show_camera_feed_button, 6, 0, 1, 2)
        self.layout.addLayout(self.button_group, 1, 0, 1, 2)
        self.layout.addWidget(self.plot_canvas, 2, 0, 4, 2)

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
        self.monitor_curve = self.plot_canvas.plot(pen='b')
        self.locked_position = 0
        self.locked_position_curve = self.plot_canvas.plot(pen=pg.mkPen('r', style=Qt.DashLine))

        self.x_plot = self.x_canvas.plot(pen='r')
        self.x_fit_plot = self.x_canvas.plot(pen=pg.mkPen('b', style=Qt.DashLine))
        self.y_plot = self.y_canvas.plot(pen='r')
        self.y_fit_plot = self.y_canvas.plot(pen=pg.mkPen('b', style=Qt.DashLine))

        # DATA STORAGE FOR MONITORING
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
        self.recall_surface_btn.clicked.connect(self._recall_surface)

        # Variable storage
        self.locked_position_profile_x = None
        self.locked_position_profile_y = None
        self.CameraHandler = None

        # hide the video feed by default
        self.video_view.hide()
        self.x_canvas.hide()
        self.y_canvas.hide()

    def _on_close_camera_button_clicked(self):
        if hasattr(self, "camera"):
            self.camera.Close()
            print("Camera closed!")
        else:
            print("No camera to close!")

    def _on_camera_settings_button_clicked(self):
        """
        Initialise and open the settings panel.
        :return:
        """
        self.settings_panel = SettingsPanel()
        self.settings_panel.show()

    def _on_initialise_button_clicked(self):
        self.current_z = 0
        self.last_movement = 0

        # Check if the camera is already initialised
        if hasattr(self, "camera"):
            self.camera.Close()

        # LOAD SETTINGS
        config_path = Path(__file__).parent / "autofocus_config.json"
        with open(config_path, "r") as f:
            self.settings = json.load(f)

        if self.settings["test_mode"]:
            import os
            os.environ["PYLON_CAMEMU"] = "1"

        self.camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
        self.camera.Open()

        if self.settings["test_mode"]:
            self.camera.TestImageSelector.Value = "Off"
            # Enable custom test images
            self.camera.ImageFileMode.Value = "On"
            # Load custom test image from disk
            print(str(Path(__file__).parent / 'test-data'))
            self.camera.ImageFilename.Value = str(Path(__file__).parent / 'test-data')

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
        self.video_view.resize(int(self.camera.Width.Value/4), int(self.camera.Height.Value/4))
        self.video_view.setAspectLocked(True)

        # z-movement parameters
        self.max_movement = self.settings["max_movement"]
        self.update_interval = self.settings["update_interval_s"]

        # instantiate callback handler
        self.CameraHandler = ImageHandler(self.camera)
        # register with the pylon loop
        self.camera.RegisterImageEventHandler(self.CameraHandler, pylon.RegistrationMode_ReplaceAll, pylon.Cleanup_None)

        # reset guesses
        self.CameraHandler.guessx = None
        self.CameraHandler.guessy = None

    def _on_lock_button_clicked(self):
        if self.lock_button.isChecked():
            # make sure camera starts grabbing
            if not self.camera.IsGrabbing():
                self.CameraHandler.fit_profiles = True
                self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
                time_to_wait = 5*float(self.exposure_time_ms)/1000
                print(f'Free-run acquisition started! Waiting for {time_to_wait} seconds.')
                time.sleep(time_to_wait) # give the camera time to acquire the first image

            if self.recall_focus_button.isChecked():
                # pass because we don't need to recalculate the lock position.
                pass
            else:
                # calculate the lock position
                self.locked_position = self._calculate_position(self.CameraHandler.guessx, self.CameraHandler.guessy)
                self.locked_position_profile_x = self.CameraHandler.x_projection
                self.locked_position_profile_y = self.CameraHandler.y_projection

                self.locked_position_guess_x = self.CameraHandler.guessx
                self.locked_position_guess_y = self.CameraHandler.guessy

                # self.get_lock_position()

            self.lock_button.setText("Definitely focused!")
            self.lock_button.setStyleSheet("font: italic bold; color: white; background-color: green;")
        elif not self.lock_button.isChecked():
            self.lock_button.setStyleSheet("font: italic;")
            self.lock_button.setText("Definitely focus?")
            if self.camera.IsGrabbing() and not self.monitor_button.isChecked() and not self.show_camera_feed_button.isChecked():
                self.camera.StopGrabbing()
                self.CameraHandler.fit_profiles = False
                print('Free-run acquisition stopped!')
        pass

    def _on_monitor_button_clicked(self):
        if self.monitor_button.isChecked():
            self.CameraHandler.fit_profiles = True
            self.ptr = 0
            # Check if the camera is grabbing or the timer is active (i.e. if the lock is already engaged)
            if self.camera.IsGrabbing():
                pass
            else:
                self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
                print('Free-run acquisition started!')
            if not self.timer.isActive():
                self.timer.start(int(self.update_interval*1000))

            # Clear the graph whenever monitor is restarted
            self.data = []
            self.time = []
        if not self.monitor_button.isChecked() and not self.lock_button.isChecked() and not self.show_camera_feed_button.isChecked():
            self.camera.StopGrabbing()
            print('Free-run acquisition stopped!')
            self.CameraHandler.fit_profiles = False
            self.timer.stop()

    def _on_show_camera_feed_button_clicked(self):
        # start acquisition and timer if not already started
        if self.show_camera_feed_button.isChecked():
            self.adjustSize()
            self.resize(self.max_size[0], self.max_size[1])
            self.video_view.show()
            self.x_canvas.show()
            self.y_canvas.show()
            if not self.camera.IsGrabbing():
                self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)
                print('Free-run acquisition started!')
            if not self.timer.isActive():
                self.timer.start(int(self.update_interval*1000))
        else:
            self.video_view.hide()
            self.x_canvas.hide()
            self.y_canvas.hide()
            self.adjustSize()
            self.resize(self.min_size)

        pass

    def _update_plots_and_position(self):
        # update plots
        if self.show_camera_feed_button.isChecked():
            self.video_canvas.setImage(self.CameraHandler.img)
            self.x_plot.setData(self.CameraHandler.x_projection)
            self.y_plot.setData(self.CameraHandler.y_projection)
            if self.lock_button.isChecked() or self.monitor_button.isChecked():
                self.x_fit_plot.setData(
                    self.CameraHandler.x_fit)
                self.y_fit_plot.setData(self.CameraHandler.y_fit)
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

            if np.abs(self.required_movement) > self.max_movement:  # change back to 0.4
                print("Movement too big. No movement.")
                # Disengage the lock button
                self.lock_button.setChecked(False)
                self.lock_button.setStyleSheet("font: italic bold; color: white; background-color: red;")
                self.lock_button.setText("Definitely NOT focused!")

                # TODO: here need to add what to do if autofocus fails. Possibly find surface and attempt to lock again?
            else:
                self.last_movement = self.required_movement
                if np.abs(self.required_movement)*1000 > 0:
                    try:
                        self.mmc.setRelativeXYZPosition(0, 0, self.required_movement)
                    except:
                        pass

        # clear data if too large
        # TODO: value below should NOT be hardcoded.
        if len(self.time) * self.settings["update_interval_s"] > 60:
            self.time = []
            self.data = []
            self.ptr = 0

        self.ptr += 1
        return

    def _calculate_position(self, guessx, guessy):
        polyfit = [self.settings["p2"], self.settings["p1"], self.settings["p0"]]
        calculated_position = -np.polyval(polyfit, guessx[2] - guessy[2])
        return calculated_position

    def _stop_autofocus(self):
        if self.lock_button.isChecked():
            self.lock_button.setChecked(False)

    # TODO: check if this work on the microscope.
    def _recall_surface(self):
        """
        Command to look for a surface.
        It is called after the stage is moved significantly in xy, or the objective lowered than raised.
        It is useful to take into account the fact that the sample does not sit perfectly horizontal.
        """
        max_travel_um = self.settings["recall_surface_range_um"]
        step_travel_um = self.settings["recall_surface_step_um"]

        if self.CameraHandler is None:
            print("Camera handler is none. Could not acquire.")
            pass
        else:
            # If camera was grabbing, stop.
            if self.camera.IsGrabbing():
                self.camera.StopGrabbing()
            # Now need to acquire a z-stack
            try:
                current_z = self.mmc.getZPosition()
            except:
                current_z = 0

            # generate an array of movements
            num_movements = (max_travel_um*2)/step_travel_um
            z_movements = np.linspace(-max_travel_um, max_travel_um, int(num_movements))
            pixel_distances = []

            self.CameraHandler.fit_profiles = False  # disable this for now - we don't need to fit anything
            self.camera.StartGrabbing(pylon.GrabStrategy_OneByOne, pylon.GrabLoop_ProvidedByInstantCamera)

            # get the target profiles and normalisation factors
            normalisation_factor_x = np.max(self.CameraHandler.locked_position_profile_x)
            normalisation_factor_y = np.max(self.CameraHandler.locked_position_profile_y)

            target_profile_x = self.locked_position_profile_x  / normalisation_factor_x
            target_profile_y = self.locked_position_profile_y / normalisation_factor_y

            # loop through the z-movements
            for movement in z_movements:
                self.mmc.setZPosition(current_z+movement)

                current_profile_x = self.CameraHandler.x_projection / normalisation_factor_x
                current_profile_y = self.CameraHandler.y_projection / normalisation_factor_y

                difference_x = target_profile_x - current_profile_x
                difference_y = target_profile_y - current_profile_y

                mean_distance_squared_x = np.mean(np.power(difference_x, 2))
                mean_distance_squared_y = np.mean(np.power(difference_y, 2))

                current_pixel_distance = mean_distance_squared_x + mean_distance_squared_y

                pixel_distances.append(current_pixel_distance)

                # FIXME: can be made WAYY more elegant, but for testing ok.
                # essentially at some point we will hit the same profile as the target, which should have a very
                # small error. We can stop there without continuing.
                # could also try to do this with fitting?

                if current_pixel_distance < 0.01:
                    break

            self.camera.StopGrabbing()

            # get the index of the smallest value
            index_smallest = np.where(pixel_distances == np.min(pixel_distances))

            # calculate surface position
            surface_position = current_z + z_movements[index_smallest[0][0]]

            # final move to the position closest to the surface.
            self.mmc.setZPosition(surface_position)

            # set fit profiles to true again
            self.CameraHandler.guessx = self.locked_position_guess_x
            self.CameraHandler.guessy = self.locked_position_guess_y
            self.CameraHandler.fit_profiles = True


def test_function():
    app = QApplication([])
    widget = AutofocusWidget()

    # settings = {"exposure_time": 100, "gain": 1, "roi": [0, 0, 1528, 1528], "p1": 1, "p0": 0}
    #
    # widget = SettingsPanel(settings)
    widget.show()
    app.exec()
    return widget


if __name__ == "__main__":
    # mmc = CMMCorePlus.instance()
    # mmc.loadSystemConfiguration()  # load demo configuration
    test_function()

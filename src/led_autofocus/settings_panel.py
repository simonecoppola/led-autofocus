from qtpy.QtWidgets import (QApplication, QWidget, QVBoxLayout, QPushButton,
                            QLabel, QLineEdit, QHBoxLayout, QGridLayout)
import json
from pathlib import Path

class SettingsPanel(QWidget):
    def __init__(self, current_settings=None):
        super().__init__()
        # Set window title
        self.setWindowTitle("LED Autofocus Settings")

        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        # get path to the function

        self.config_path = Path(__file__).parent / "autofocus_config.json"
        with open(self.config_path, "r") as f:
            current_settings = json.load(f)

        # Create input values
        self.exposure_time = InputLine("Exposure time (ms)", current_settings["exposure_time_ms"])
        self.gain = InputLine("Gain", current_settings["gain"])
        self.width = InputLine("Width", current_settings["width"])
        self.height = InputLine("Height", current_settings["height"])
        self.offset_x = InputLine("Offset X", current_settings["offset_x"])
        self.offset_y = InputLine("Offset Y", current_settings["offset_y"])
        self.max_movement = InputLine("Max movement (um)", current_settings["max_movement"])
        self.p2 = InputLine("p2", current_settings["p2"])
        self.p1 = InputLine("p1", current_settings["p1"])
        self.p0 = InputLine("p0", current_settings["p0"])

        # Title labels
        self.camera_settings_label = QLabel("Camera settings")
        self.camera_settings_label.setStyleSheet("font: bold; font-size: 16px;")
        self.calibration_settings_label = QLabel("Calibration settings")
        self.calibration_settings_label.setStyleSheet("font: bold; font-size: 16px;")
        self.calibration_settings_hint = QLabel("Calibration line is y = p2*x^2 + p1*x + p0")
        self.calibration_settings_hint.setContentsMargins(0, 0, 0, 0)

        self.update_settings_button = QPushButton("Update settings")
        self.update_settings_button.setMinimumHeight(50)

        self.layout.addWidget(self.camera_settings_label)
        self.layout.addWidget(self.exposure_time)
        self.layout.addWidget(self.gain)
        self.layout.addWidget(self.width)
        self.layout.addWidget(self.height)
        self.layout.addWidget(self.offset_x)
        self.layout.addWidget(self.offset_y)
        self.layout.addWidget(self.calibration_settings_label)
        self.layout.addWidget(self.calibration_settings_hint)
        self.layout.addWidget(self.p2)
        self.layout.addWidget(self.p1)
        self.layout.addWidget(self.p0)
        self.layout.addWidget(self.max_movement)
        self.layout.addWidget(self.update_settings_button)

        self.update_settings_button.clicked.connect(self.update_settings)

    def update_settings(self):
        settings = {
            "exposure_time_ms": int(self.exposure_time.get_value()),
            "gain": int(self.gain.get_value()),
            "width": int(self.width.get_value()),
            "height": int(self.height.get_value()),
            "offset_x": int(self.offset_x.get_value()),
            "offset_y": int(self.offset_y.get_value()),
            "p2": self.p2.get_value(),
            "p1": self.p1.get_value(),
            "p0": self.p0.get_value(),
            "max_movement": self.max_movement.get_value()
        }

        with open(self.config_path, "w") as f:
            json.dump(settings, f)

        print("Settings updated")

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

    def get_value(self):
        return float(self.input.text())


def test_function():
    app = QApplication([])
    widget = SettingsPanel()

    widget.show()
    app.exec()
    return widget

if __name__ == "__main__":
    test_function()
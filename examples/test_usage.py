from pymmcore_plus import CMMCorePlus
from qtpy.QtWidgets import QApplication
from led_autofocus import AutofocusWidget

# import the plate_mda module
app = QApplication([])  # open application

# set up mmc
mmc = CMMCorePlus.instance()
mmc.loadSystemConfiguration()

autofocus_widget = AutofocusWidget()
autofocus_widget.show()

# execute
app.exec_()
# 🚨LED-Autofocus
LED-based autofocus built for the [Holden Lab](https://holdenlab.github.io/) Openframe microscope at the University of Warwick. Heavily inspired by [Rahmani _et al_ (2024)](https://opg.optica.org/oe/fulltext.cfm?uri=oe-32-8-13331&id=548369) and [Lightley _et al_ (2023)](https://onlinelibrary.wiley.com/doi/10.1111/jmi.13219).

The repository hosts code which makes a widget where the focus position can be monitored and locked when used alongside a [pymmcore-plus](https://pymmcore-plus.github.io/pymmcore-plus/) instance. The widget leverages [pyqtgraph](https://pyqtgraph.readthedocs.io/) for fast plotting. 

No specific qt backend is specified in the requirements, so you will have to install it yourself. qtpy is used as an abstraction layer.

**Important:** the code was developed to be used with a Basler camera, so it uses the Basler pylon for camera control.

To install, clone the repository, navigate to it in the terminal and then run `pip install .`

Example and calibration codes are in the `examples` folder. More information on components, build instructions and 
usage is in the documentation: https://simonecoppola.github.io/led-autofocus/

The project is very much in the early stages so bugs are likely.

<p align="center">
  <img src="docs/resources/widget_window.png"/>
</p>

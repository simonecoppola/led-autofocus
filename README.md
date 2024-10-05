# 🚨LED-Autofocus
LED-based autofocus built for the [Holden Lab](https://holdenlab.github.io/) Openframe microscope at the University of Warwick. Heavily inspired by [Rahmani _et al_ (2024)](https://opg.optica.org/oe/fulltext.cfm?uri=oe-32-8-13331&id=548369) and [Lightley _et al_ (2023)](https://onlinelibrary.wiley.com/doi/10.1111/jmi.13219).

The repository hosts code which makes a widget where the focus position can be monitored and locked when used alongside a [pymmcore-plus](https://pymmcore-plus.github.io/pymmcore-plus/) instance. The widget leverages [pyqtgraph](https://pyqtgraph.readthedocs.io/) for fast plotting. 

No specific qt backend is specified in the requirements, so you will have to install it yourself. qtpy is used as an abstraction layer.

**Important:** the code was developed to be used with a Basler camera, so it uses the Basler pylon for camera control.

To install, clone the repository, navigate to it in the terminal and then run `pip install .`

Example and calibration codes are in the `examples` folder.

The project is very much in the early stages so bugs are likely.

## 📃List of Components
|                   | Part Name                         | Part Number                                                                                                                                              | Cost (GBP) | Notes                                                                 |
| ----------------- | --------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |------------| --------------------------------------------------------------------- |
|                   | Dichroic mirror (800nm shortpass) | 69-220                                                                                                                                                   | 145.35     |                                                                       |
|                   | 50:50 beamsplitter                | [BSW26R](https://www.thorlabs.com/thorproduct.cfm?partnumber=BSW26R)                                                                                     | 274.65     |                                                                       |
| Imaging Path      |                                   |                                                                                                                                                          |            |                                                                       |
|                   | Basler ace2 Camera                | [a2A2590-60umBAS](https://www.edmundoptics.com/p/basler-ace2-a2a2590-60umbas-monochrome-usb3-basic-camera/44055/)                                        | 262.25     | Ponjavic et al. have shown a Raspberry Pi camera can be used instead. |
|                   | Tube Lens (f=200)                 | [AC254-200-B](https://www.thorlabs.com/thorproduct.cfm?partnumber=AC254-200-B)                                                                           | 82.92      |                                                                       |
|                   | Cylindrical Lens (f=300)          | LJ1558RM-B                                                                                                                                               | 104.54     |                                                                       |
|                   | Shortpass filter (Cut-off 800nm)  | [FESH0800](https://www.thorlabs.com/thorproduct.cfm?partnumber=FESH0800)                                                                                 | 115        |                                                                       |
|                   | Longpass filter (Cut-off 800nm)   | FELH0800                                                                                                                                                 | 119        |                                                                       |
|                   |                                   |                                                                                                                                                          |            |                                                                       |
| Illumination Path |                                   |                                                                                                                                                          |            |                                                                       |
|                   | 850nm LED                         | [M850L3](https://www.thorlabs.com/thorproduct.cfm?partnumber=M850L3)                                                                                     | 205.27     | Significantly cheaper LEDs could be used.                             |
|                   | LED Power Supply                  | [Thorlabs - LEDD1B T-Cube LED Driver, 1200 mA Max Drive Current (Power Supply Not Included)](https://www.thorlabs.com/thorproduct.cfm?partnumber=LEDD1B) | 228        | Significantly cheaper power supplies could be used.                   |
|                   | Collimating lens (f=100)          | LA1207-B                                                                                                                                                 | 27.08      |                                                                       |
|                   | Pinhole/iris                      | P400K                                                                                                                                                    | 62.9       |                                                                       |
|                   | Steering mirror (2x)              | BB1-EO3                                                                                                                                                  | 129.96     |                                                                       |
|                   |                                   |                                                                                                                                                          |            |                                                                       |
|                   |                                   |                                                                                                                                                          | 1771.09    |                                                                       |
## 🛠️Build Instructions
Coming soon

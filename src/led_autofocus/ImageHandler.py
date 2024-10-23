import pypylon.pylon as py
import numpy as np
# handle exception trace for debugging
# background loop
from ._fit_utilities import fit_gaussian, get_initial_guess, Gaussian1D
import traceback

class ImageHandler(py.ImageEventHandler):
    def __init__(self, cam, fit_profiles=False):
        super().__init__()
        self.img = np.zeros((cam.Height.Value, cam.Width.Value), dtype=np.uint8)

        # allocate space for rows and cols projections
        self.x_projection = np.zeros(cam.Width.Value, dtype=np.uint8)
        self.y_projection = np.zeros(cam.Height.Value, dtype=np.uint8)

        # allocate space for x and y fits
        self.x_fit = np.zeros(4, dtype=np.float32)
        self.y_fit = np.zeros(4, dtype=np.float32)

        self.fit_profiles = fit_profiles
        self.guessx = None
        self.guessy = None

        # allocate space for timestamp
        self.timestamp = np.zeros(1, dtype=np.float32)


    def OnImageGrabbed(self, camera, grabResult):
        """ from pylon demo - adapted for my needs
            we get called on every image
            !! this code is run in a pylon thread context
            always wrap your code in the try .. except to capture
            errors inside the grabbing as this can't be properly reported from
            the background thread to the foreground python code
        """
        try:
            if grabResult.GrabSucceeded():
                self.img = grabResult.Array
                self.x_projection = np.divide(self.img.sum(axis=0), np.max(self.img.sum(axis=0)))
                self.y_projection = np.divide(self.img.sum(axis=1), np.max(self.img.sum(axis=1)))
                self.timestamp = grabResult.TimeStamp

                if self.fit_profiles:
                    # TODO: this SHOULD NOT BE HARDCODED
                    lower_bounds_x = [0.16645382983589865, 1873.5450515219172, 168.1517174143853, 0.6842269616042337]
                    upper_bounds_x = [0.296276181455513, 1887.9348764886313, 297.8739296981674, 0.8774971871010732]

                    lower_bounds_y = [0.3044611777064768, 1051.7494828481322, 185.65333974112244, 0.5134878312787584]
                    upper_bounds_y = [0.42110617483966817, 1209.3809746481377, 462.2202979953617, 0.6639392163134101]

                    if self.guessx is None:
                        self.guessx = [sum(x)/2 for x in zip(lower_bounds_x, upper_bounds_x)]
                        self.guessy = [sum(x)/2 for x in zip(lower_bounds_y, upper_bounds_y)]

                    self.guessx = fit_gaussian(
                                        np.linspace(0, self.x_projection.shape[0], self.x_projection.shape[0]), self.x_projection,
                                        self.guessx, bounds= (lower_bounds_x, upper_bounds_x))
                    self.guessy = fit_gaussian(np.linspace(0, self.y_projection.shape[0], self.y_projection.shape[0]), self.y_projection,
                                        self.guessy, bounds=(lower_bounds_y, upper_bounds_y))

                    self.x_fit = Gaussian1D(np.linspace(0, self.x_projection.shape[0], self.x_projection.shape[0]), *self.guessx)
                    self.y_fit = Gaussian1D(np.linspace(0, self.y_projection.shape[0], self.y_projection.shape[0]), *self.guessy)
            else:
                raise RuntimeError("Grab Failed")
        except Exception as e:
            traceback.print_exc()

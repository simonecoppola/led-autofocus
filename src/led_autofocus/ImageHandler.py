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
                # check image contents
                # print(f"Image grabbed at {now.time()}, shape: {img.shape}")
                # print("New image grabbed at", now.time())
                self.img = grabResult.Array
                self.x_projection = self.img.sum(axis=0)
                self.y_projection = self.img.sum(axis=1)
                self.timestamp = grabResult.TimeStamp

                # print(self.timestamp)
                # print(self.fit_profiles)

                if self.fit_profiles:
                    if self.guessx is None:
                        self.guessx = get_initial_guess(self.x_projection)
                        self.guessy = get_initial_guess(self.y_projection)

                    # print(self.guessx)
                    self.guessx = fit_gaussian(np.linspace(0, self.x_projection.shape[0], self.x_projection.shape[0]), self.x_projection,
                                        self.guessx)
                    self.guessy = fit_gaussian(np.linspace(0, self.y_projection.shape[0], self.y_projection.shape[0]), self.y_projection,
                                        self.guessy)

                    self.x_fit = Gaussian1D(np.linspace(0, self.x_projection.shape[0], self.x_projection.shape[0]), *self.guessx)
                    self.y_fit = Gaussian1D(np.linspace(0, self.y_projection.shape[0], self.y_projection.shape[0]), *self.guessy)
            else:
                raise RuntimeError("Grab Failed")
        except Exception as e:
            traceback.print_exc()

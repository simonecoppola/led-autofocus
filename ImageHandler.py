import pypylon.pylon as py
import numpy as np

# handle exception trace for debugging
# background loop
import traceback
import datetime
import time
import random

class ImageHandler(py.ImageEventHandler):
    def __init__(self, cam):
        super().__init__()
        self.img = np.zeros((cam.Height.Value, cam.Width.Value), dtype=np.uint8)

    def OnImageGrabbed(self, camera, grabResult):
        """ we get called on every image
            !! this code is run in a pylon thread context
            always wrap your code in the try .. except to capture
            errors inside the grabbing as this can't be properly reported from
            the background thread to the foreground python code
        """
        try:
            if grabResult.GrabSucceeded():
                # check image contents
                img = grabResult.Array
                now = datetime.datetime.now()
                # print(f"Image grabbed at {now.time()}, shape: {img.shape}")
                print("New image grabbed at", now.time())
                self.img = img
            else:
                raise RuntimeError("Grab Failed")
        except Exception as e:
            traceback.print_exc()


def BackGroundLoopSample(cam):
    # instantiate callback handler
    handler = ImageHandler(cam)
    # register with the pylon loop
    cam.RegisterImageEventHandler(handler, py.RegistrationMode_ReplaceAll, py.Cleanup_None)

    # fetch some images with background loop
    cam.StartGrabbingMax(100, py.GrabStrategy_LatestImages, py.GrabLoop_ProvidedByInstantCamera)
    while cam.IsGrabbing():
        # random exposuretime changes every 100ms
        print(handler.img.mean())
        pass
    cam.StopGrabbing()
    cam.DeregisterImageEventHandler(handler)

    return handler.img_sum


if __name__ == "__main__":
    cam = py.InstantCamera(py.TlFactory.GetInstance().CreateFirstDevice())
    cam.Open()
    cam.ExposureTime.SetValue(100*1000)
    BackGroundLoopSample(cam)
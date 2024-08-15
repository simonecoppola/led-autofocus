import time
from pypylon import pylon
import matplotlib.pyplot as plt

# enable emulation
import os
os.environ["PYLON_CAMEMU"] = "1"

camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())


camera.Open()
camera.Width.Value = 1528
camera.Height.Value = 1528
camera.TestImageSelector.Value = "Off"
# Enable custom test images
camera.ImageFileMode.Value = "On"
# Load custom test image from disk
camera.ImageFilename.Value = 'C:\\Users\\u1870329\\Documents\\GitHub\\led-autofocus\\test-data\\'

camera.StartGrabbing(pylon.GrabStrategy_OneByOne)
i = 0
print('Starting to acquire')
t0 = time.time()
while camera.IsGrabbing():
    grab = camera.RetrieveResult(100, pylon.TimeoutHandling_ThrowException)
    if grab.GrabSucceeded():
        i += 1
    if i == 100:
        plt.imshow(grab.Array)
        plt.show()
        break



print(f'Acquired {i} frames in {time.time()-t0:.0f} seconds')
camera.Close()
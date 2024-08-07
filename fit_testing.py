import numpy as np
from numba import jit
import numpy as np
import time
from scipy.optimize import curve_fit


def Gaussian1D(x: np.ndarray, i0: float, x0: float, sx: float, amp: float) -> np.ndarray:
    """
    Model for a 1D Gaussian, will be used to fit the x and y projections of the PSF.
    :param x: array of x values to be passed into the function
    :param i0: constant offset
    :param x0: peak position
    :param sx: standard deviation
    :param amp: amplitude
    :return: the Gaussian function at the given x values
    """
    x0 = float(x0)
    eq = i0+amp*np.exp(-((x-x0)**2/2/sx**2))
    return eq


def fit_gaussian(x: np.ndarray, profile:np.ndarray, init_guess: list) -> np.ndarray:
    """
    Fit a Gaussian to a profile
    :param x: x-coordinate of the profile
    :param profile: y-coordinate of the profile
    :param init_guess: initial guess, [i0, x0, sx, amp]
    :return: final guess, [i0, x0, sx, amp]
    """
    popt, pcov = curve_fit(Gaussian1D, x, profile, p0=init_guess)
    return popt


def get_image_projection_fits(image, initial_guess_rows, initial_guess_cols):
    """
    Get the x and y projections of an image and fit a Gaussian to each
    :param image:
    :return:
    """
    # Calculate the projection over the columns
    x_projection = image.sum(axis=0)
    y_projection = image.sum(axis=1)

    # Make an array of values as long as x_projection
    x_vals = np.linspace(0, x_projection.shape[0], x_projection.shape[0])
    y_vals = np.linspace(0, y_projection.shape[0], y_projection.shape[0])

    # Now fit a gaussian to each projection
    x_fit = fit_gaussian(x_vals, x_projection, initial_guess_rows)
    y_fit = fit_gaussian(y_vals, y_projection, initial_guess_cols)

    return x_fit, y_fit


def make_astigmatic_psf(x, y, sigma_x, sigma_y):
    g = np.exp(-((x**2 / (2 * sigma_x**2)) + (y**2 / (2 * sigma_y**2))))
    return g


if __name__ == "__main__":
    # Generating 2D grids 'x' and 'y' using meshgrid with 10 evenly spaced points from -1 to 1
    x, y = np.meshgrid(np.linspace(-1, 1, 100), np.linspace(-1, 1, 100))
    g = make_astigmatic_psf(x, y, 1, 0.5)

    x_projection = g.sum(axis=0)
    y_projection = g.sum(axis=1)

    x_fit, y_fit = get_image_projection_fits(g, [0, 0, 0.5, 1], [0, 0, 0.5, 1])

    x_vals = np.linspace(0, x_projection.shape[0], x_projection.shape[0])
    y_vals = np.linspace(0, y_projection.shape[0], y_projection.shape[0])

    import matplotlib.pyplot as plt

    # create ax and fig for two subplots
    fig, ax = plt.subplots(2, 1)
    ax[0].plot(x_vals, x_projection)
    ax[0].plot(x_vals, Gaussian1D(x_vals, *x_fit), '--')
    ax[1].plot(y_vals, y_projection)
    ax[1].plot(x_vals, Gaussian1D(x_vals, *y_fit), '--')

    ax[0].set_title('X Projection')
    ax[1].set_title('Y Projection')

    plt.show()


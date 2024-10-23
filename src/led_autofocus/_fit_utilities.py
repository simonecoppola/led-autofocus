import numpy as np
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


def fit_gaussian(x: np.ndarray, profile: np.ndarray, init_guess: list, bounds=(-np.inf, np.inf)) -> np.ndarray or None:
    """
    Fit a Gaussian to a profile
    :param x: x-coordinate of the profile
    :param profile: y-coordinate of the profile
    :param init_guess: initial guess, [i0, x0, sx, amp]
    :return: final guess, [i0, x0, sx, amp] or None if the fit failed
    """
    # popt, pcov = curve_fit(Gaussian1D, x, profile, p0=init_guess, bounds=bounds)
    popt, pcov, infodic, mesg, ier = curve_fit(Gaussian1D, x, profile, p0=init_guess, bounds=bounds, full_output=True)

    if ier > 4:
        # if ier is greater than 4, the fit failed - return None.
        return None
    else:
        return popt

def get_initial_guess(profile: np.ndarray) -> list:
    """
    Get initial guess for Gaussian fit
    :param profile: profile to fit
    :return: initial guess, [i0, x0, sx, amp]
    """
    i0 = np.min(profile)
    x0 = np.argmax(profile)
    sx = x0/4
    amp = np.max(profile) - i0
    return [i0, x0, sx, amp]

if __name__ == "__main__":
    # Test the Gaussian fitting
    x = np.linspace(0, 100, 100)
    y = Gaussian1D(x, 0, 50, 10, 100)
    y = y + np.random.normal(0, 1, y.shape)

    guess = get_initial_guess(y)
    fit = fit_gaussian(x, y, guess)

    print(fit)
    print(guess)
    print(fit - guess)
    print(np.sum((fit - guess)**2))
    print(np.sum((fit - guess)**2) < 1e-3)
    print("Test passed")
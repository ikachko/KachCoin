import numpy as np
import matplotlib.pyplot as plt

my_a = 5 # Качко
my_b = 4 # Илья

def elliptic_draw(a, b, save_plot=False):
    y, x = np.ogrid[-5:5:100j, -5:5:100j]
    plt.contour(x.ravel(), y.ravel(), pow(y, 2) - pow(x, 3) - x * a - b, [0])
    plt.grid()
    if save_plot:
        plt.savefig("ikachko_elliptic_curve.png")
elliptic_draw(my_a, my_b, save_plot=True)

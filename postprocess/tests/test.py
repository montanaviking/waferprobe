__author__ = 'test'
import matplotlib.pyplot as plt
from scipy.interpolate import UnivariateSpline
import numpy as np
x = np.linspace(3, -3, 100)
y = np.exp(-x**2) + 0.1 * np.random.randn(100)
plt.plot(x, y, 'ro', ms=5)



spl = UnivariateSpline(np.flipud(x), y, s=0)
sply = np.flipud(spl(x))
#xs = np.linspace(-3, 3, 100)
plt.plot(x, sply, 'g', lw=3)

print(x)
print(spl(x))

spl.set_smoothing_factor(0.5)
sply=spl(x)
plt.plot(x, sply, 'b', lw=3)
plt.show()


import xlay

import matplotlib.pyplot as plt
import numpy as np

curve = xlay.Curve()

curve.lineby(10)
curve.bendby(5, 45)
curve.lineby(10)
curve.bendby(5, -45)
curve.lineby(10)
curve.bendby(5, 90)
curve.lineby(10)
curve.bendby(5, 90)
curve.lineby(30)
curve.bendby(5, 30)
curve.lineby(5)
curve.bendby(5, 60)
curve.lineby(16)
curve.bendby(5, 90)
curve.lineby(2)

x, y, z = np.array([p.loc for p in curve.points()]).T

ax = plt.subplot(111, aspect="equal")
ax.plot(z, x)

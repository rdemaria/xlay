import xlay

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

curve = xlay.Curve()
a = 1.5e-3 / 2 / np.pi * 360
l = 3.4
d = 0.866

curve.lineby(4)
curve.bendby(l, a)
for i in range(5):
    curve.lineby(d)
    curve.bendby(l, a)

curve.lineby(4)

x, y, z = np.array([p.loc for p in curve.points()]).T

ax = plt.subplot(111, aspect="auto")
ax.plot(z, x, color="r")
ax.plot(z, x - 0.01, "--r")
ax.plot(z, -x, color="b")
ax.plot(z, -x + 0.01, "--b")
ax.plot(z, x * 0, color="g")

for i in range(6):
    rect = patches.Rectangle(
        (4 + i * (l + d), -0.2), l, 0.4, facecolor="none", edgecolor="k"
    )
    ax.add_patch(rect)

x, _, z = np.array([seg.start.loc for s, seg in curve.segments])[1:, :].T
ax.plot(z, x, "or")
ax.plot(z, -x, "ob")
ax.plot(z, x * 0, "og")

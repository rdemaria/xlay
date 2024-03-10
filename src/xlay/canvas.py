"""
name is for access
label is for presentation


element.render() -> generate list poses of primitives
canvas.draw_primitive() -> extract points or mesh from primitive and draw using style

"""

import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.path as mpath


from matplotlib import patches
import numpy as np


def resolve_style(style, primitive, layer, name):
    if style is None:
        style = {}
    if layer in style:
        style = {**style, **style[layer]}
    if name in style:
        style = {**style, **style[name]}
    if primitive.__class__.__name__ in style:
        style = {**style, **style[primitive.__class__.__name__]}
    return style


class SimpleProjection:
    def __init__(self, axes="xy", scale=1, origin=[0, 0]):
        self.axes = axes
        if np.isscalar(scale):
            self.scale = [scale, scale]
        else:
            self.scale = scale
        self.origin = origin
        mapping = {"x": 0, "y": 1, "z": 2}
        self.idx0 = mapping[axes[0]]
        self.idx1 = mapping[axes[1]]

    def transform(self, points):
        """Transform points from 3D to 2D

        Args:
            points np.ndarray 3xN: N 3D points in columns
        """
        x = points[self.idx0] * self.scale[0] + self.origin[0]
        y = points[self.idx1] * self.scale[1] + self.origin[1]
        return x, y


class Canvas2D:
    default_style = {}

    def __init__(
        self,
        projection="xy",
        origin=[0, 0],
        scale=1,
        units="m",
        style=None,
        xlabel=None,
        ylabel=None,
        fig=None,
        ax=None,
    ):
        if isinstance(projection, str):
            self.projection = SimpleProjection(axes=projection, origin=origin, scale=scale)
        else:
            self.projection = projection
        if style is None:
            style = Canvas2D.default_style
        self.style = style
        self.units = units
        if xlabel is None:
            xlabel = f"{self.projection.axes[0]} [{self.units}]"
        self.xlabel = xlabel
        if ylabel is None:
            ylabel = f"{self.projection.axes[1]} [{self.units}]"
        self.ylabel = ylabel
        self.artists = {}
        self.elements = {}
        self.set_figure(fig, ax)

    def add(self, element):
        self.elements[element.name] = element
        return self

    def set_figure(self, fig, ax):
        if fig is not None:
            self.fig = fig
            if ax is None:
                self.ax = fig.gca()
            else:
                self.ax = ax
        if fig is None:
            if ax is None:
                self.fig, self.ax = plt.subplots()
                self.ax.set_aspect("equal")
                self.draw()
                self.fig.show()
            else:
                self.ax = ax
                self.fig = ax.get_figure()

    def clear(self):
        for key, artists in self.artists.items():
            for artist in artists:
                artist.remove()

    def draw(self, style=None):
        self.clear()
        self.ax.set_xlabel(self.xlabel)
        self.ax.set_ylabel(self.ylabel)
        if style is None:
            style = self.style
        for key, element in self.elements.items():
            for primitive in element.render(style):
                artists = self.draw_primitive(primitive, style)
                self.artists[key] = artists
        self.fig.show()

    def draw_primitive(self, primitive, style):
        style = resolve_style(
            style, primitive, primitive.layer, primitive.name
        )
        if style.get("visible", True):
            if primitive.element is None:
                artists=self.draw_pose(primitive, style)
            else:
                method=f"draw_{primitive.element.__class__.__name__}".lower()
                artists = getattr(self, method)( primitive, style)
            return artists
        else:
            return []

    def draw_pose(self, pose, style):
        x, y = self.projection.transform(pose.matrix[:3, 3])
        return [self.ax.text(x, y, pose.name)]

    def draw_line(self, primitive, style):
        points = primitive.matrix@primitive.element.points
        x, y = self.projection.transform(points)
        return [self.ax.plot(x, y, **style)]

    def draw_polyline(self, primitive, style):
        points = primitive.matrix@primitive.element.points
        x, y = self.projection.transform(points)
        return [self.ax.plot(x, y, **style)]

    def draw_polygon(self, primitive, style):
        points = primitive.matrix@primitive.element.points
        xy = np.array(self.projection.transform(points)).T
        patch = mpatches.Polygon(xy, edgecolor='k',facecolor='none', **style)
        print(xy.shape)
        self.ax.add_patch(patch)
        return [patch]

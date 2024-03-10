"""
A Point describe a position in a 3D space: location and orientation.
A Point can hold an assembly to specify the position of that assembly.

Manages reference frames and transformations.


Potential decision: 
- Pose(pose) copies the matrix


"""

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

class Element:
    def __init__(self, name=None, label=None, layer=None):
        self.name = name
        self.label = label
        self.layer = layer

    def __getitem__(self, key):
        if key in self.__dict__:
            return self.__dict__[key]
        else:
            try:
               return getattr(self, key)
            except AttributeError:
                raise KeyError(f"{self} has no attribute {key}")

    def at(self, name=None, pose=None):
        if pose is None:
            return Pose(name=name, element=self)
        else:
            return pose.new(name=name,element=self)

    def render(self, style):
        return [Pose(name=self.name, element=self)]

    def draw2d(self, style=None, projection='xy'):
        from .canvas import Canvas2D
        canvas = Canvas2D(projection=projection, style=style)
        canvas.add(self)
        canvas.draw()
        return canvas


class Pose:
    def __init__(
        self,
        x=0,
        y=0,
        z=0,
        dx=[1, 0, 0],
        dy=[0, 1, 0],
        dz=[0, 0, 1],
        matrix=None,
        loc=None,
        rot=None,
        element=None,
        name=None,
        label=None,
        layer=None,
    ):
        if matrix is None:
            if loc is not None:
                x, y, z = loc
            if rot is not None:
                dx, dy, dz = rot.T
            self.matrix = np.array(
                [
                    [dx[0], dy[0], dz[0], x],
                    [dx[1], dy[1], dz[1], y],
                    [dx[2], dy[2], dz[2], z],
                    [0, 0, 0, 1],
                ],
                dtype=float,
            )
        elif isinstance(matrix, np.ndarray):
            self.matrix = matrix
        elif hasattr(matrix, "matrix"):
            self.matrix = matrix.matrix
        self.name = name
        self.label = label
        self.layer = layer
        self.element = element

    def __repr__(self):
        args = []
        if self.name is not None:
            args.append(f"{self.name!r}:")
        if self.element is not None:
            if self.element.name is not None:
                args.append(f"{self.element.name!r}")
            else:
                args.append(f"{self.element!r}")
        args.append(f"at {self.loc}")
        return f"<{' '.join(args)}>"

    def at(self, name, pose):
        return self.clone(name=name, matrix=pose.matrix@self.matrix)

    def __getitem__(self, path):
        path =path.split("/")
        key=path[0]
        name=f"{self.name}/{key}"
        res=self.element[key].at(name, pose=self)
        if len(path)>1:
            return res[path[1]]
        else:
            return res

    def __getattr__(self, key):
        try:
            return self[key]
        except AttributeError:
            raise AttributeError(f"{self} has no attribute {key}")

    @property
    def x(self):
        return self.matrix[0, 3]

    @x.setter
    def x(self, value):
        self.matrix[0, 3] = value

    @property
    def y(self):
        return self.matrix[1, 3]

    @y.setter
    def y(self, value):
        self.matrix[1, 3] = value

    @property
    def z(self):
        return self.matrix[2, 3]

    @z.setter
    def z(self, value):
        self.matrix[2, 3] = value

    @property
    def dx(self):
        return self.matrix[:3, 0]

    @dx.setter
    def dx(self, value):
        self.matrix[:3, 0] = value

    @property
    def dy(self):
        return self.matrix[:3, 1]

    @dy.setter
    def dy(self, value):
        self.matrix[:3, 1] = value

    @property
    def dz(self):
        return self.matrix[:3, 2]

    @dz.setter
    def dz(self, value):
        self.matrix[:3, 2] = value

    @property
    def loc(self):
        return self.matrix[:3, 3]

    @loc.setter
    def loc(self, value):
        self.matrix[:3, 3] = value

    @property
    def loc4(self):
        return self.matrix[:, 3]

    @property
    def rot(self):
        return self.matrix[:3, :3]

    @rot.setter
    def rot(self, value):
        self.matrix[:3, :3] = value

    @property
    def n(self):
        return self.new()

    @property
    def c(self):
        return self.clone()

    def __mul__(self, other):
        matrix = self.matrix.copy()
        matrix[:3, :3] = matrix[:3, :3] @ other.matrix[:3, :3]
        return self.clone(matrix=matrix)

    def __matmul__(self, other):
        matrix = self.matrix.copy()
        matrix = matrix @ other.matrix
        return self.clone(matrix=matrix)

    def __add__(self, other):
        matrix = self.matrix.copy()
        matrix[:3, 3] += other.matrix[:3, 3]
        return self.clone(matrix=matrix)

    def tx(self, x):
        self.matrix = np.dot(
            self.matrix,
            np.array([[1, 0, 0, x], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
        )
        return self

    def ty(self, y):
        self.matrix = np.dot(
            self.matrix,
            np.array([[1, 0, 0, 0], [0, 1, 0, y], [0, 0, 1, 0], [0, 0, 0, 1]]),
        )
        return self

    def tz(self, z):
        self.matrix = np.dot(
            self.matrix,
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, z], [0, 0, 0, 1]]),
        )
        return self

    def rx(self, angle):
        angle_rad = np.radians(angle)
        cx = np.cos(angle_rad)
        sx = np.sin(angle_rad)
        self.matrix = np.dot(
            self.matrix,
            np.array(
                [
                    [1, 0, 0, 0],
                    [0, cx, -sx, 0],
                    [0, sx, cx, 0],
                    [0, 0, 0, 1],
                ]
            ),
        )
        return self

    def ry(self, angle):
        angle_rad = np.radians(angle)
        cx = np.cos(angle_rad)
        sx = np.sin(angle_rad)
        self.matrix = np.dot(
            self.matrix,
            np.array(
                [
                    [cx, 0, sx, 0],
                    [0, 1, 0, 0],
                    [-sx, 0, cx, 0],
                    [0, 0, 0, 1],
                ]
            ),
        )
        return self

    def rz(self, angle):
        angle_rad = np.radians(angle)
        cx = np.cos(angle_rad)
        sx = np.sin(angle_rad)
        self.matrix = np.dot(
            self.matrix,
            np.array(
                [
                    [cx, -sx, 0, 0],
                    [sx, cx, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1],
                ]
            ),
        )
        return self

    def clone(self, **kwargs):
        """Return a full clone of the current pose"""
        newargs = {**self.__dict__, **kwargs}
        return Pose(**newargs)

    def new(self, **kwargs):
        """Return a new pose with the same matrix as self"""
        return Pose(matrix=self.matrix, **kwargs)

    def distance(self, pose):
        return np.linalg.norm(self.matrix[:3, 3] - pose.matrix[:3, 3])

    def render(self, style):
        from .primitives import Text
        primitives = []
        if style.get("labels", False):
            primitives.append(
                Text(text=self.name).at(self,pose=self))
        if style.get("center.visible", True):
            primitives.append(self.new(name=self.name))
        if self.element is not None:
            for primitive in self.element.render(style):
                primitives.append(
                    primitive.at(name=f"{self.name}/{primitive.name}",pose=self)
                )
        return primitives

    def draw2d(self, style=None, projection='xy'):
        from .canvas import Canvas2D
        canvas = Canvas2D(projection=projection, style=style)
        canvas.add(self)
        canvas.draw()
        return canvas



class Frame(Element):
    def __init__(self, name, *parts, data=None, parent=None, prototype=None):
        self.name = name
        self.parts = {el.name: el for el in parts} # Poses of the parts
        self.data = data  # other metadata
        self.parent = parent  # name of the parent assembly
        self.prototype = prototype  # if it has been cloned

    def clone(self, **kwargs):
        data = {**self.__dict__, **kwargs}
        return super().__class__(prototype=self, **data)

    def __getitem__(self, path):
        path =path.split("/")
        key=path[0]
        res=self.parts[key]
        if len(path)>1:
            return res[path[1]]
        else:
            return res

    def render(self,style=None):
        primitives = []
        for part in self.parts.values():
            primitives.extend(part.render(style=style))
        return primitives


"""
The module represents the geometric primitives for layout design.

name: for retrieval [unique]
label: for display
layer:
- center
- axis
- extremes
- region
- bounding box

styles are managed by canvas

Curves are parametric curves. They are defined by a start point, a tangent and a list of segments. The segments are:
   - lineto: end
   - arcto: radius, end
   - lineby: length
   - bendby: length, angle, roll

Curve query:
    - point: return the point at a given accumulated path length s
    - points: return a set of points covering the curve at a give accuracy
    - tangent: return the tangent at a given accumulated path length s

Primitive api:

points(): return points
mesh(): return mesh
 
"""

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from .pose import Element, Pose


class Point:
    def __init__(self, point=None, name=None, label=None, layer=None):
        """
        Point shape must be (3,) or (4,)
        """
        self.arr = np.ones(4, dtype=float)
        if point is None:
            self.arr[:3] = 0
        else:
            self.arr[:3] = point[:3]
        self.name = name
        self.label = label
        self.layer = layer

    def loc(self):
        return self.arr[:3]

    def __repr__(self):
        args = []
        if self.name is not None:
            args.append(f"name={self.name}")
        return f"Point({self.arr[:3]},{', '.join(args)})"


class Points:
    def __init__(self, points, name=None, label=None, layer=None):
        """
        stored in 4xN vector with 1 in the last row
        """
        if hasattr(points, "shape"):
            if points.shape[0] == 3:
                self.arr = np.ones((4, points.shape[1]), dtype=float)
                self.arr[:3] = points
            elif points.shape[0] == 4:
                self.arr = points
            else:
                raise ValueError("Points shape must be (3,N) or (4,N)")
        self.name = name
        self.label = label
        self.layer = layer

    def __repr__(self):
        args = []
        if self.name is not None:
            args.append(f"name={self.name}")
        return f"<Points({self.arr[:3]},{', '.join(args)})>"


class Line(Element):
    def __init__(self, start, end, name=None, label=None, layer=None):
        if not isinstance(start, Pose):
            start = Pose(*start)
        if not isinstance(end, Pose):
            end = Pose(*end)
        self.start = start
        self.end = end
        self.name = name
        self.label = label
        self.layer = layer

    def __repr__(self):
        args = []
        if self.name is not None:
            args.append(f"name={self.name}")
        return f"Line({self.start},{self.end},{', '.join(args)})"

    def length(self):
        return self.start.distance(self.end)

    def point(self, s):
        pstart = self.start.loc
        pend = self.end.loc
        rstart = Rotation.from_matrix(self.start.rot)
        rend = Rotation.from_matrix(self.end.rot)
        rot = Slerp([0, self.length], [rstart, rend])(s)
        return Pose(loc=pstart + s * (pend - pstart), rot=rot.as_matrix())

    def points(self):
        return np.array([self.start.loc4, self.end.loc4]).T


class Rectangle(Element):
    def __init__(self, name=None, lx=1, ly=1, label=None, layer=None):
        self.lx = lx
        self.ly = ly
        self.name = name
        self.label = label
        self.layer = layer

    def __repr__(self):
        args = []
        if self.name is not None:
            args.append(f"name={self.name}")
        return f"Rectangle(lx={self.lx},lx={self.ly})"

    @property
    def center(self):
        return Pose(name=f"{self.name}/center")

    @property
    def ul(self):
        return Pose(name=f"{self.name}/ul", x=-self.lx / 2, y=self.ly / 2)

    @property
    def ur(self):
        return Pose(name=f"{self.name}/ur", x=self.lx / 2, y=self.ly / 2)

    @property
    def ll(self):
        return Pose(name=f"{self.name}/ll", x=-self.lx / 2, y=-self.ly / 2)

    @property
    def lr(self):
        return Pose(name=f"{self.name}/lr", x=self.lx / 2, y=-self.ly / 2)

    @property
    def left(self):
        return Pose(name=f"{self.name}/left", x=-self.lx / 2)

    @property
    def right(self):
        return Pose(name=f"{self.name}/right", x=self.lx / 2)

    @property
    def top(self):
        return Pose(name=f"{self.name}/top", y=self.ly / 2)

    @property
    def bottom(self):
        return Pose(name=f"{self.name}/bottom", y=-self.ly / 2)

    def points(self):
        return np.array(
            [
                pp.loc4
                for pp in (self.ul, self.ur, self.lr, self.ll, self.ul)
            ]
        )

    def render(self, style):
        primitives = []
        points = np.array(
            [
                pp.loc4
                for pp in (self.ul, self.ur, self.lr, self.ll, self.ul)
            ]
        ).T
        print(points)
        primitives.append(Polygon(points=points).at(name=self.name))
        return primitives


class Polyline(Element):
    def __init__(self, name=None, points=None, label=None, layer=None):
        self.name = name
        self.points = points
        self.label = label
        self.layer = layer

    def __repr__(self):
        return f"Polyline({self.points})"



class Polygon(Polyline):
    def __init__(self, name=None, points=None, label=None, layer=None):
        self.name = name
        self.points = points
        self.label = label
        self.layer = layer

    def __repr__(self):
        return f"Polygon({self.points})"


class Bend:
    """
    Defined by starting pose:
       plane: in xz rolled by roll angle
       angle: angle spanned by the arc
       length: length of the arc

    """

    def __init__(
        self, start, length, angle, roll=0, name=None, label=None, layer=None
    ):
        self.start = start
        self.angle = angle
        self.length = length
        self.roll = roll
        self.name = name
        self.label = label
        self.layer = layer

    def __repr__(self):
        args = []
        if self.name is not None:
            args.append(f"name={self.name}")
        if self.roll != 0:
            args.append(f"roll={self.roll}")
        return (
            f"Bend({self.start},{self.length},{self.angle},{', '.join(args)})"
        )

    def point(self, s):
        # using mad-x formula
        fullangle = np.deg2rad(self.angle)
        radius = self.length / fullangle
        alpha = fullangle * s / self.length
        ca = np.cos(alpha)
        sa = np.sin(alpha)
        psi = np.deg2rad(self.roll)
        cp = np.cos(psi)
        sp = np.sin(psi)
        R = np.array([radius * (ca - 1), 0, radius * sa])
        S = np.array([[ca, 0, -sa], [0, 1, 0], [sa, 0, ca]])
        T = np.array([[cp, -sp, 0], [sp, cp, 0], [0, 0, 1]])
        Ti = np.array([[cp, sp, 0], [-sp, cp, 0], [0, 0, 1]])
        R = T @ R
        S = T @ S @ Ti
        loc = self.start.rot @ R + self.start.loc
        rot = self.start.rot @ S
        return Point(loc=loc, rot=rot)

    def points(self, steps=5):
        s = np.linspace(0, self.length, steps)
        return [self.point(si) for si in s]

    @property
    def end(self):
        return self.point(self.length)


class Ellipse:
    def __init__(self, center, radius_x, radius_y):
        self.center = center
        self.radius_x = radius_x
        self.radius_y = radius_y


class Circle:
    def __init__(self, center, radius):
        self.center = center
        self.radius = radius


# curve segments
class LineTo:
    def __init__(self, end):
        self.end = end

    def __repr__(self):
        return f"LineTo({self.end})"

    def get_segment(self, start):
        length = start.distance(self.end)
        return Line(start, self.end), length, self.end


class ArcTo:
    def __init__(self, radius, end):
        self.radius = radius
        self.end = end

    def __repr__(self):
        return f"ArcTo({self.radius},{self.end})"

    def get_segment(self, start):
        raise NotImplementedError


class LineBy:
    def __init__(self, length, axis="z"):
        self.length = length
        self.axis = axis

    def __repr__(self):
        args = []
        args.append(f"length={self.length}")
        if self.axis != "z":
            args.append(f"axis={self.axis}")
        return f"LineBy({','.join(args)})"

    def get_segment(self, start):
        end = getattr(start.new(), f"t{self.axis}")(self.length)
        return Line(start, end), self.length, end


class BendBy:
    def __init__(self, length=0, angle=0, roll=0, axis="xz"):
        self.length = length
        self.angle = angle
        self.roll = roll
        self.axis = axis

    def __repr__(self) -> str:
        args = []
        if self.length != 0:
            args.append(f"length={self.length}")
        if self.angle != 0:
            args.append(f"angle={self.angle}")
        if self.roll != 0:
            args.append(f"roll={self.roll}")
        if self.axis != "z":
            args.append(f"axis={self.axis}")
        return f"BendBy({','.join(args)})"

    def get_segment(self, start):
        segment = Bend(start, self.length, self.angle, self.roll)
        return segment, self.length, segment.end


class Curve:
    """
    A smooth curve is a parametric curve defined by a start pose and a list of segments.

    The curve is smooth is all points and tangents are continuous.

    Each s is associated to one and one-only pose.

    """

    @classmethod
    def from_svgpath(cls, svgpath):
        pass

    def __init__(self, start=None, specs=None, s_start=0.0, lookup_ds=1.0):
        if start is None:
            start = Point()
        if specs is None:
            specs = []
        self.start = start
        self.end = start
        self.s_start = s_start
        self.s_end = s_start
        self.specs = specs
        self.segments = []
        self.lookup_ds = lookup_ds
        self.lookup_end = s_start
        self.lookup = []
        for spec in specs:
            self.add_spec(spec)

    def add_spec(self, spec):
        seg_start = self.s_end
        segment, length, end = spec.get_segment(self.end)
        self.s_end += length
        self.end = end
        self.segments.append((seg_start, segment))
        idx = len(self.segments) - 1
        self.specs.append(spec)
        steps = int((self.s_end - self.lookup_end) / self.lookup_ds)
        self.lookup += [idx] * steps
        self.lookup_end += steps * self.lookup_ds
        self.length = self.s_end - self.s_start

    def point(self, s):
        if s < self.s_start or s > self.s_end:
            raise ValueError(
                f"Curve point out of range {s} not in [{self.s_start},{self.s_end}]"
            )
        lookup_idx = int((s - self.s_start) // self.lookup_ds)
        seg_idx = self.lookup[lookup_idx]
        segment_s, segment = self.segments[seg_idx]
        if s < segment_s:
            segment_s, segment = self.segments[seg_idx - 1]
        return segment.point(s - segment_s)

    def lineto(self, end):
        self.add_spec(LineTo(end))

    def arcto(self, radius, end):
        self.add_spec(ArcTo(radius, end))

    def lineby(self, length, axis="z"):
        self.add_spec(LineBy(length, axis))

    def bendby(self, length=0, angle=0, roll=0, axis="z"):
        self.add_spec(BendBy(length, angle, roll, axis))

    def points(self, steps=5):
        points = []
        for _, segment in self.segments:
            points += segment.points()
        return points

    def tangent(self, s):
        pass

    def to_svgpath(self):
        pass

    def __repr__(self):
        return f"Curve: {self.s_start}, {self.s_end}, {len(self.segments)} segments"


class Box:
    def __init__(self, center, size, name=None, label=None, layer=None):
        self.center = center
        self.size = size
        self.name = name
        self.label = label
        self.layer = layer


class Tube:
    def __init__(self, curve, sections, name=None, label=None, layer=None):
        self.curve = curve
        self.sections = sections
        self.name = name
        self.label = label
        self.layer = layer


class Text:
    def __init__(self, text, name=None, label=None, layer=None):
        self.text = text
        self.name = name
        self.label = label
        self.layer = layer


class Field:
    def __init__(self, point, vectors, name=None, label=None, layer=None):
        self.point = point
        self.vectors = vectors
        self.name = name
        self.label = label
        self.layer = layer


class Mesh:
    def __init__(self, points, faces, name=None, label=None, layer=None):
        self.points = points
        self.faces = faces
        self.name = name
        self.label = label
        self.layer = layer

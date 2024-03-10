"""
The library models the layout of a beamline.

A Layout is a collections of elements in positions and orientations.

A Pose is a position and orientation in 3D space and can contain a reference to an element.

An element specify an object in space, could be primitive, such as a square or complex such as an assembly of elements.

An assembly is a container of parts specified by elements at a given pose.

pose[key] returns  Pose(element[key],name=f"{pose.name}/{key}").



An element has a render method that returns a list of primitives and their poses for diplsaying the element.


Points:
Single point (3,) ,(4.) or (3,1), (4,1)
Multipole pints (3,N), (4,N)

.points() -> return (4,N)
.poses() -> return list of poses
.point(s) -> for curves return Pose at s


Style:
  style is used by render to determine what primitives to emit draw
  style is used by draw_primitive to determine how to draw primitive 

"""

import importlib.metadata

__version__ = importlib.metadata.version(__package__ or __name__)

from .assembly import Assembly, Magnet
from .layout import Beamline, Layout, Node, Env
from .pose import Pose, Element, Frame
from .primitives import (Bend, Box, Circle, Curve, Ellipse, Line, Polygon,
                         Polyline, Rectangle, Text, Tube)
from .canvas import Canvas2D

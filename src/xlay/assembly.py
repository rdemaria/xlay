""" 
The assembly is a container of parts. A part is elemement/component at a given pose. 
"""

from typing import Any


class Assembly:
    @classmethod
    def from_yamldata(cls, name, data):
        kwargs = {}
        for attr in data:
            for kattr, vattr in attr.items():
                kwargs[kattr] = vattr

        return cls(name=name, **kwargs)

    def __init__(self, name=None, parts=None, data=None, parent=None, prototype=None):
        self.name = name
        self.parts = parts  # Poses with assemblies
        self.data = data  # other metadata
        self.parent = parent  # name of the parent assembly
        self.prototype = prototype  # if it has been cloned

    def at(self, point, name=None):
        return point.clone(type=self, name=name)

    def clone(self, **kwargs):
        data = {**self.__dict__, **kwargs}
        return super().__class__(prototype=self, **data)

    def __repr__(self):
        return f"{self.name}: {self.show_yaml()}"

    def show_yaml(self):
        attr = [str(self.prototype)]
        for k, v in self.__dict__.items():
            if k not in ["name", "parts", "prototype"]:
                if v is not None:
                    attr.append(f"{k}: {v}")
        return f"[{', '.join(attr)}]"


class Magnet(Assembly):
    def __init__(self, length=0, angle=0, tilt=0, aperture=None, name=None, parts=None):
        self.name = name
        self.length = length
        self.angle = angle
        self.tilt = tilt
        self.aperture = aperture
        super().__init__(name=name, prototype=self.__class__.__name__, parts=parts)


class Bend(Magnet):
    def __init__(self, length=0, angle=0, tilt=0, aperture=None, name=None):
        super().__init__(length, angle, tilt, aperture, name, parts=dict())


class Quadrupole(Magnet):
    def __init__(self, length=0, angle=0, tilt=0, aperture=None, name=None):
        super().__init__(length, angle, tilt, aperture, name, parts=dict())


class Region(Assembly):
    def __init__(self, length=0, angle=0, tilt=0, profiles=None, name=None, parts=None):
        self.name = name
        self.length = length
        self.angle = angle
        self.tilt = tilt
        self.profiles = profiles
        super().__init__(name=name, **parts)

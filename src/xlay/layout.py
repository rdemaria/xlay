"""

Nodes can be repeat in YAML but internally they are unique.


ll=xl.Layout.from_yaml('lattice1.yaml')
ll['MBB'][MB.1'] -> return the node



ll/'MBB/MB.1/center' -> returns a point object in the frame of the layout
ll/'MBB'/'MB.1'/'center' -> same as above?
ll['MBB']/'MB.1/center' -> returns a point object in the frame of MBB
ll['MBB'][MB.1'] -> return the node object
ll/'MBB'/'MB.1' -> return a point with the associated assembly

Questions:
ll['MBB/MB.1'] -> return the assembly object
ll['MBB/MB.1'] -> return point

"""

import yaml

from .pose import Pose
from .assembly import Assembly, Magnet, Bend, Quadrupole


class Node:
    def __init__(
        self,
        name,
        assembly,
        at=None,
        from_=None,
        ref="middle",
        ref_angle=None,
        ref_length=None,
        ref_roll=None,
        transform=None,
    ):
        self.name = name
        self.assembly = assembly
        self.at = at
        self.from_ = from_
        self.ref = ref
        self.ref_angle = ref_angle
        self.ref_length = ref_length
        self.ref_roll = ref_roll
        self.transform = transform
        if self.transform is None:
            self.transform = []
        if self.ref_angle is None:
            if hasattr(assembly, "angle"):
                self.ref_angle = assembly.angle
            else:
                self.ref_angle = 0
        if self.ref_length is None:
            if hasattr(assembly, "length"):
                self.ref_length = assembly.length
            else:
                self.ref_length = 0
        if self.ref_roll is None:
            if hasattr(assembly, "roll"):
                self.ref_roll = assembly.roll
            else:
                self.ref_roll = 0

    def __repr__(self):
        return f"{self.name}: {self.assembly}, at={self.at}"


class Segment:
    def __init__(self, length, angle, roll, start):
        self.length = length
        self.angle = angle
        self.roll = roll
        self.start = start

    def __repr__(self):
        return f"Segment: {self.length}, {self.angle}, {self.roll}, {self.start}"


class Beamline:
    @classmethod
    def from_yamldata(cls, name, data):
        nodes = {}
        for nodedata in data:
            [(nodename, attrs)] = nodedata.items()
            kwargs = {}
            transform = []
            assembly = attrs[0]
            for attr in attrs[1:]:
                for kattr, vattr in attr.items():
                    if kattr in ["tx", "ty", "tz", "rx", "ry", "rz"]:
                        transform.append([kattr, vattr])
                    else:
                        kwargs[kattr] = vattr
            kwargs["transform"] = transform
            kwargs["assembly"] = assembly
            kwargs["name"] = nodename
            nodes[nodename] = Node(**kwargs)
        return cls(name=name, nodes=nodes)

    def __init__(self, name=None, nodes=None):
        self.name = name
        self.nodes = nodes

    def find_sorted_nodes(self):
        abs_start = {}
        klist = set(self.nodes.keys())
        while len(klist) > 0:
            k = klist.pop()
            node = self.nodes[k]
            if node.at is not None:
                if node.from_ is None:
                    abs_start[k] = node.at
                elif k in abs_start:
                    abs_start[k] = abs_start[node.from_] + node.at
                else:
                    klist.add(k)
        sorted_nodes = sorted(abs_start.items(), key=lambda x: x[1])
        return sorted_nodes

    def find_segments(self):
        sorted_nodes = self.find_sorted_nodes()
        k, node_start = sorted_nodes.pop(0)
        node = self.nodes[k]
        cur_s = node_start + node.ref_length
        cur_angle = self.nodes[k].ref_angle
        cur_roll = self.nodes[k].ref_roll
        segments = [Segment(node.ref_length, cur_angle, cur_roll, node_start)]
        for k, node_start in self.find_sorted_nodes():
            node = self.nodes[k]
            if node_start < cur_s:  # node overlaps with previous node
                if node.ref_angle != cur_angle or node.ref_roll != cur_roll:
                    raise ValueError(
                        f"Node {k} overlaps with previous node but has different angle or roll"
                    )
                else:
                    node_end = node_start + node.ref_length
                    if node_end > cur_s:
                        segments[-1].length = node_end - cur_s
            cur_angle = node.ref_angle
            cur_roll = node.ref_roll
            cur_s += node.ref_length
            segments.append(Segment(node.ref_length, cur_angle, cur_roll, cur_s))
        return segments

    def __repr__(self):
        return f"{self.name}: {self.show_yaml()}"

    def show_yaml(self):
        if len(self.nodes) < 4:
            nodes = ", ".join(self.nodes)
        else:
            kk = list(self.nodes.keys())
            nodes = ", ".join(kk[:2] + ["..."] + kk[-2:])
        return f"[Sequence, {nodes}]"

    def __getitem__(self, key):
        return self.nodes[key]


class Layout:
    @classmethod
    def from_yaml(cls, filename):
        yamldata = yaml.safe_load(open("lattice1.yaml"))
        vars = {}
        data = {"vars": vars}
        for k, v in yamldata.items():
            if type(v) == str:  # variable definition
                vars[k] = v
            elif type(v) == list:  # assembly definition
                obj = assemblies[v[0]].from_yamldata(k, v[1:])
                data[k] = obj
        layout = cls(data)
        return layout

    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"Layout: {len(self.data)-1} elements"

    def __getitem__(self, key):
        return self.data[key]

    def show(self):
        maxkey = max([len(k) for k in self.data.keys()])
        fmt = f"{{:<{maxkey}}}: {{}}"
        for k, v in self.data.items():
            if k != "vars":
                print(fmt.format(k, v.show_yaml()))


assemblies = {
    "Magnet": Magnet,
    "Bend": Bend,
    "Quadrupole": Quadrupole,
    "Assembly": Assembly,
    "Beamline": Beamline,
}



class Env:
    classes={}

    def __init__(self):
        self.elements = {}
        #self.mgr=xdeps.Manager()

    def add(self, element):
        if isinstance(element, str):
            element=self.parse(element)
        else:
            element=element

    def to_string(self):
        yield NotImplementedError

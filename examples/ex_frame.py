import xlay

r = xlay.Rectangle("R1", lx=1, ly=1)

f = xlay.Frame(
    "F",
    r.at("a").tx(1).rz(45),
    r.at("b").tx(-1).rz(45),
    r.at("c").ty(1).rz(45),
    r.at("d").ty(-1).rz(45),
)

print(f.parts["a"].element.left)
print(f.parts["a"].left) # left in the frame of "a"
print(f['a'].left) # left in the frame of "a"
print(f["a/left"]) # left in the frame of "a"

canvas=f.draw2d()

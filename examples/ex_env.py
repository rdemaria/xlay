import xlay

env=xlay.Env()
env.add(xlay.Rectangle("R1",lx=1,ly=1))

env2=xlay.Env.from_json(env.to_json())
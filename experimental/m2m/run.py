from pyecore.resources.xmi import XMIResource
from transfo_example import transfo

# generated using
# https://github.com/kolovos/datasets/blob/master/github-mde/ghmde.ecore
# as input metamodel
import ghmde


# quick model def
a = ghmde.Repository(name='repo')
f = ghmde.File(path='test')
a.files.append(f)

b = ghmde.Repository()

resource = XMIResource()
resource.append(a)
resource.append(b)

# run transfo (multi-root)
transfo.run(ghmde=resource)

print(transfo.inputs.ghmde.contents[0])
assert transfo.outputs.other == transfo.primary_output
assert transfo.outputs.other == transfo.outputs[0]
print(transfo.outputs.other.contents)
print(transfo.outputs.test2.contents)


# run transfo (single direct root)
transfo.run(ghmde=a)

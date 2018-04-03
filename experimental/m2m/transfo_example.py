import motra
import ghmde


# Transfo definition
transfo = motra.Transformation('ghmde_refact',
                               inputs=['ghmde'],
                               outputs=['other', 'test2'])


@transfo.main
def main(inputs, outputs):
    print('in main')
    print(inputs.ghmde.contents)
    for o in motra.objects_of_kind(inputs.ghmde, ghmde.Repository):
        test_dispatch(o)


@transfo.mapping(when=lambda self: self.name is not None)
def test1(self: ghmde.Repository) -> ghmde.Repository:
    print('changing name', result is self, self.name)
    result.name = self.name
    self.name += '_toto'


@transfo.mapping(output_model='test2',
                 when=lambda self: self.name is None)
def test2(self: ghmde.Repository) -> ghmde.Repository:
    result.name = 'from_empty_' + str(self)


@transfo.disjunct(mappings=[test1, test2])
def test_dispatch(self: ghmde.Repository) -> ghmde.Repository:
    pass

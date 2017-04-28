class ModelTypeMixin:
    """Implements the model filter by returning all elements of a certain element type."""

    element_type = None

    def filtered_elements(self, model):
        # TODO: yield from model.elements.where(isinstance(e, self.element_type))
        yield from ()

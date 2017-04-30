"""Support for generation for models based on pyecore."""


class ModelTypeMixin:
    """
    Implements the model filter by returning all elements of a certain element type.
    
    Use this mixin to add the model type iteration faility to another generator task class.
    
    Attributes:
        element_type: Ecore type to be searched in model and to be iterated over.
    """

    element_type = None

    def filtered_elements(self, model):
        return (e for e in model.eAllContents() if isinstance(e, self.element_type))

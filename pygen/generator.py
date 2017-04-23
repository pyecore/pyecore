import logging
import os

import pathlib
import types

from typing import Iterator, Iterable

from pyecore.ecore import EModelElement, EPackage

_logger = logging.getLogger(__name__)


class Generator:
    """
    Code generator from PyEcore models.
    
    Attributes:
        tasks: List of generator tasks to be processed as part of this generator.
    """

    def __init__(self, tasks: Iterable['Task']):
        self.tasks = list(tasks)

    def __repr__(self):
        return '{name}({args})'.format(name=self.__class__.__name__,
                                       args=', '.join('{!r}'.format(t) for t in self.tasks))

    def generate(self, model: EPackage, outfolder: str):
        """Generate artifacts for given model."""

        outfolder = os.path.abspath(outfolder)
        _logger.info('Generating code to {!r}.'.format(outfolder))

        context = types.SimpleNamespace(
            generator=self,
            model=model,
            outfolder=outfolder,
        )

        for task in self.tasks:
            task.execute(context)


class Task:
    """
    Generator task applied to a set of model elements.
    
    This is the base class for tasks, its implementation is not doing anything. Note that derived
    classes are explicitly allowed to extend the context object with task specific data.
    """

    def execute(self, context):
        """Apply this task to all corresponding elements in model."""

        for element in self.elements(context):
            self.apply_to(element, context)

    def apply_to(self, element: EModelElement, context):
        """
        Application of this generation step to given model element.
        
        Args:
            element: Model element for which to generate code.
            context: Container with information useful during generation.
        """

    def elements(self, context) -> Iterator[EModelElement]:
        """
        Iterator over model elements to execute this task for.
        
        Args:
            context: Container with information useful during generation.

        Returns:
            Iterator over processable elements.
        """
        yield from ()

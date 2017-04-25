import logging
import os

import pathlib
import types
import typing

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

        for task in self.tasks:
            for element in task.filtered_elements(model):
                context = task.get_context(
                    generator=self,
                    outfolder=outfolder,
                    model=model,
                    element=element
                )
                task.execute(context)


class Task:
    """
    Generator task applied to a set of model elements.
    
    This is the base class for tasks, its implementation is not doing anything. Note that derived
    classes are explicitly allowed to extend the context object with task specific data.
    """

    def execute(self, context):
        """Apply this task to all corresponding elements in model."""

    def get_context(self, **kwargs):
        """Return context dictionary built from keyword arguments."""
        kwargs['task'] = self
        return kwargs

    def filtered_elements(self, model: EPackage) -> Iterator[EModelElement]:
        """Iterator over model elements to execute this task for."""
        yield from ()


class FileTask(Task):
    """Generator task creating a file."""

    def get_context(self, **kwargs):
        filepath = self.get_filepath(**kwargs)
        return super().get_context(filepath=filepath, **kwargs)

    def get_filepath(self, element: EModelElement, **kwargs):
        """
        Output file path, relative to root folder.
        """
        return '{}.py'.format(element.eURIFragment())

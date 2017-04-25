import logging
import os

import pathlib
import types
import typing

from typing import Iterator, Iterable

from pyecore.ecore import EModelElement, EPackage, EObject

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
        """Apply this task to model element in context."""

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
        file_path = self.get_filepath(**kwargs)
        return super().get_context(file_path=file_path, **kwargs)

    def get_filepath(self, **kwargs):
        """Output file path, relative to root folder."""
        raise NotImplementedError()


class TemplateFileTask(FileTask):
    """Create a file from model element via a text template."""

    templates_folder = '.'

    def execute(self, context):
        generated_file_path = os.path.join(context['outfolder'], context['file_path'])
        template_path = os.path.join(self.templates_folder, context['template_name'])
        _logger.info('Template {!r} --> {!r}'.format(template_path, generated_file_path))
        self.execute_template(context, template_path, generated_file_path)

    def get_context(self, **kwargs):
        template_name = self.get_template_name(**kwargs)
        return super().get_context(template_name=template_name)

    def get_template_name(self, **kwargs):
        raise NotImplementedError()

    def execute_template(self, context, template_path, generated_file_path):
        raise NotImplementedError()

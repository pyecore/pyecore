"""Support for generation for models based on pyecore."""
import os

from pyecore.ecore import EPackage
from pygen.jinja import JinjaTask, JinjaGenerator


class EcoreTask(JinjaTask):
    """
    Base class for Jinja based generation of Pyecore models.
    
    Attributes:
        element_type: Ecore type to be searched in model and to be iterated over.
    """

    element_type = None

    def filtered_elements(self, model):
        """Return iterator based on `element_type`."""
        return (e for e in model.eAllContents() if isinstance(e, self.element_type))

    @classmethod
    def folder_path_for_package(cls, package: EPackage):
        parent = package.eContainer()
        if parent:
            return os.path.join(cls.folder_path_for_package(parent), package.name)
        return package.name


class EcorePackageInitTask(EcoreTask):
    """Generation of package init file from Ecore model with Jinja2."""

    template_name = 'package.py'
    element_type = EPackage

    def relative_path_for_element(self, element: EPackage):
        folder = self.folder_path_for_package(element)
        path = os.path.join(folder, '__init__.py')
        return path


class EcorePackageModuleTask(EcoreTask):
    """Generation of package model from Ecore model with Jinja2."""

    template_name = 'module.py'
    element_type = EPackage

    def relative_path_for_element(self, element: EPackage):
        folder = self.folder_path_for_package(element)
        path = os.path.join(folder, '{}.py'.format(element.name))
        return path


class EcoreGenerator(JinjaGenerator):
    """Generation of static ecore model classes."""

    tasks = [
        EcorePackageInitTask,
        EcorePackageModuleTask,
    ]

    templates_path = 'templates'

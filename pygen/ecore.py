"""Support for generation for models based on pyecore."""
import os

import itertools
import jinja2

from pyecore.ecore import EPackage, EOrderedSet, EClass, EEnum, EModelElement, EReference
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
        if isinstance(model, self.element_type):
            yield model
        yield from (e for e in model.eAllContents() if isinstance(e, self.element_type))

    @classmethod
    def folder_path_for_package(cls, package: EPackage):
        """Returns path to folder holding generated artifact for given element."""
        parent = package.eContainer()
        if parent:
            return os.path.join(cls.folder_path_for_package(parent), package.name)
        return package.name

    @staticmethod
    def filename_for_element(package: EPackage):
        """Returns generated file name."""
        raise NotImplementedError

    def relative_path_for_element(self, element: EPackage):
        path = os.path.join(self.folder_path_for_package(element),
                            self.filename_for_element(element))
        return path


class EcorePackageInitTask(EcoreTask):
    """Generation of package init file from Ecore model with Jinja2."""

    template_name = 'package.py.tpl'
    element_type = EPackage

    @staticmethod
    def filename_for_element(package: EPackage):
        return '__init__.py'


class EcorePackageModuleTask(EcoreTask):
    """Generation of package model from Ecore model with Jinja2."""

    template_name = 'module.py.tpl'
    element_type = EPackage

    @staticmethod
    def imported_classifiers(p: EPackage):
        """Determines which classifiers have to be imported into given package."""
        classes = {c for c in p.eClassifiers if isinstance(c, EClass)}

        supertypes = itertools.chain(*(c.eAllSuperTypes() for c in classes))
        imported = {c for c in supertypes if c.ePackage is not p}

        attributes = itertools.chain(*(c.eAttributes for c in classes))
        attributes_types = (a.eType for a in attributes)
        enum_types = (t for t in attributes_types if isinstance(t, EEnum))
        imported |= {t for t in enum_types if t.ePackage is not p}

        # sort by owner package name:
        return sorted(imported, key=lambda c: c.ePackage.name)

    @staticmethod
    def classes(p: EPackage):
        """Returns classes in package in ordered by number of bases."""
        classes = (c for c in p.eClassifiers if isinstance(c, EClass))
        return sorted(classes, key=lambda c: len(set(c.eAllSuperTypes())))

    @staticmethod
    def filename_for_element(package: EPackage):
        return '{}.py'.format(package.name)

    def create_template_context(self, element, **kwargs):
        return super().create_template_context(
            element=element,
            classes=self.classes(element),
            imported_classifiers=self.imported_classifiers(element)
        )


class EcoreGenerator(JinjaGenerator):
    """Generation of static ecore model classes."""

    tasks = [
        EcorePackageInitTask(),
        EcorePackageModuleTask(),
    ]

    @staticmethod
    def test_type(value, type_):
        """Jinja test to check object type."""
        return isinstance(value, type_)

    @staticmethod
    def filter_documentation(value: EModelElement) -> str:
        annotation = value.getEAnnotation('http://www.eclipse.org/emf/2002/GenModel')
        return annotation.details.get('documentation', '') if annotation else ''

    @staticmethod
    def filter_supertypes(value: EClass):
        supertypes = ', '.join(t.name for t in value.eSuperTypes)
        return supertypes if supertypes else 'EObject, metaclass=MetaEClass'

    @staticmethod
    def filter_pyquotesingle(value: str):
        return '\'{}\''.format(value) if value is not None else ''

    @staticmethod
    def filter_pyquotetriple(value: str):
        return '"""{}"""'.format(value) if value is not None else ''

    @staticmethod
    def filter_refqualifiers(value: EReference):
        qualifiers = dict(
            ordered=value.ordered,
            unique=value.unique,
            containment=value.containment,
        )
        if value.many:
            qualifiers.update(upper=-1)

        return ', '.join('{}={}'.format(k, v) for k, v in qualifiers.items())

    def create_environment(self, **kwargs):
        """
        Return a new Jinja environment.

        Derived classes may override method to pass additional parameters or to change the template
        loader type.
        """
        environment = jinja2.Environment(
            loader=jinja2.PackageLoader('pygen', self.templates_path),
            **kwargs
        )
        environment.tests.update({
            'type': self.test_type
        })
        environment.filters.update({
            'documentation': self.filter_documentation,
            'pyquotesingle': self.filter_pyquotesingle,
            'pyquotetriple': self.filter_pyquotetriple,
            'refqualifiers': self.filter_refqualifiers,
            'supertypes': self.filter_supertypes,
        })

        from pyecore import ecore
        environment.globals.update({'ecore': ecore})

        return environment

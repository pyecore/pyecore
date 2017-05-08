"""Jinja2 support for multifile generation."""
import functools

import jinja2

from pygen.generator import TemplateGenerator, TemplateFileTask


class JinjaGenerator(TemplateGenerator):
    """Jinja2 based code generator."""

    def __init__(self, environment=None, **kwargs):
        super().__init__(**kwargs)
        self.environment = environment or self.create_environment()

        # pass Jinja environment to tasks:
        for task in self.tasks:
            task.environment = self.environment

    def create_environment(self, **kwargs):
        """
        Return a new Jinja environment.
        
        Derived classes may override method to pass additional parameters or to change the template
        loader type.
        """
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.templates_path),
            **kwargs
        )


class JinjaTask(TemplateFileTask):
    """Base class for Jinja2 based code generator tasks."""

    def __init__(self, formatter=None, **kwargs):
        super().__init__(**kwargs)
        if not formatter:
            import autopep8
            formatter = functools.partial(autopep8.fix_code, options={'max_line_length': 100})
        self.formatter = formatter
        self.environment = None

    def generate_file(self, element, filepath):
        template = self.environment.get_template(self.template_name)
        context = self.create_template_context(element=element)

        with open(filepath, 'wt') as file:
            file.write(self.formatter(template.render(**context)))

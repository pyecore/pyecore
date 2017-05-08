"""Small framework for multifile generation on top of another template code generator."""
import logging
import os

_logger = logging.getLogger(__name__)


class Generator:
    """
    Code generator from PyEcore models.
    
    Attributes:
        tasks:
            List of generator tasks to be processed as part of this generator.
        model:
            Model for which to generate code.
        outfolder: 
            Folder where code files are created.
    """

    tasks = []

    def __init__(self, **kwargs):
        if kwargs:
            raise AttributeError('Unexpected arguments: {!r}'.format(kwargs))

    def generate(self, model, outfolder):
        """Generate artifacts for given model."""

        _logger.info('Generating code to {!r}.'.format(outfolder))

        for task in self.tasks:
            for element in task.filtered_elements(model):
                task.run(element, outfolder)


class Task:
    """File generation task applied to a set of model elements."""

    def __init__(self, **kwargs):
        if kwargs:
            raise AttributeError('Unexpected arguments: {!r}'.format(kwargs))
        self._generator = None

    def run(self, element, outfolder):
        """Apply this task to model element."""
        filepath = self.relative_path_for_element(element)
        if outfolder and not os.path.isabs(filepath):
            filepath = os.path.join(outfolder, filepath)

        _logger.debug('{!r} --> {!r}'.format(element, filepath))

        self.ensure_folder(filepath)
        self.generate_file(element, filepath)

    @staticmethod
    def ensure_folder(filepath):
        dirname = os.path.dirname(filepath)
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

    def filtered_elements(self, model):
        """Iterator over model elements to execute this task for."""
        raise NotImplementedError()

    def relative_path_for_element(self, element):
        """Returns relative file path receiving the generator output for given element."""
        raise NotImplementedError()

    def generate_file(self, element, filepath):
        """Actual file generation from model element."""
        raise NotImplementedError()


class TemplateGenerator(Generator):
    templates_path = 'templates'


class TemplateFileTask(Task):
    template_name = None

    def create_template_context(self, element, **kwargs):
        context = dict(element=element)
        context.update(**kwargs)
        return context

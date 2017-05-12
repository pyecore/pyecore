import os
import shutil
from unittest import mock

import pytest

from pygen.jinja import JinjaGenerator, JinjaTask


@pytest.fixture('module', autouse=True)
def cwd_module_dir():
    # change cwd to this module's directory:
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    yield

    # reset after module goes out of scope:
    os.chdir(cwd)


@pytest.fixture
def outfolder():
    path = os.path.join('output', 'jinja')
    shutil.rmtree(path, ignore_errors=True)
    yield path
    shutil.rmtree(path, ignore_errors=False)


class MyTemplateTask(JinjaTask):
    template_name = 'test.py.tpl'

    def filtered_elements(self, model):
        # apply to all elements in "model":
        return model.elements

    def relative_path_for_element(self, element):
        return '{}.py'.format(element.name)


class MyGenerator(JinjaGenerator):
    templates_path = 'input'

    tasks = [
        MyTemplateTask()
    ]


class MyModel:
    def __init__(self, elements):
        self.elements = elements


class MyElement:
    def __init__(self, name):
        self.name = name


def test__jinja_generator__integration(outfolder):
    model = MyModel([
        MyElement('A'),
        MyElement('B'),
    ])

    generator = MyGenerator()
    generator.generate(model, outfolder)

    with open(os.path.join(outfolder, 'A.py')) as file:
        generated_text = file.read()
    assert generated_text == 'print(\'This is a test template for element A.\')'

    with open(os.path.join(outfolder, 'B.py')) as file:
        generated_text = file.read()
    assert generated_text == 'print(\'This is a test template for element B.\')'


@mock.patch.object(JinjaTask, 'create_template_context', side_effect=lambda **kwargs: kwargs)
def test__jinja_task__generate_file(mock_create_template_context):
    mock_template = mock.MagicMock()
    mock_template.render = mock.MagicMock(return_value='rendered text')
    mock_environment = mock.MagicMock()
    mock_environment.get_template = mock.MagicMock(return_value=mock_template)

    task = JinjaTask()
    task.environment = mock_environment
    task.template_name = mock.sentinel.TEMPLATE_NAME

    mock_open = mock.mock_open()
    with mock.patch('pygen.jinja.open', mock_open, create=True):
        task.generate_file(mock.sentinel.ELEMENT, 'filepath.ext')

    mock_template.render.assert_called_once_with(element=mock.sentinel.ELEMENT)
    mock_open.assert_called_once_with('filepath.ext', 'wt')
    mock_open().write.assert_called_once_with('rendered text')

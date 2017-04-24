import os
from unittest import mock

from pygen.generator import Generator, Task


def test__generator__generate__no_tasks():
    # calling empty generator not raising anything:
    Generator(tasks=()).generate(mock.sentinel.MODEL, '.')


def test__generator__generate__tasks():
    mock_task1 = mock.Mock()
    mock_task2 = mock.Mock()

    mock_manager = mock.Mock()
    mock_manager.attach_mock(mock_task1, 'task1')
    mock_manager.attach_mock(mock_task2, 'task2')

    # let first task add some information to context:
    def execute(context):
        context.new_attribute = mock.sentinel.NEW_ATTRIBUTE

    mock_task1.execute = mock.Mock(side_effect=execute)

    generator = Generator(tasks=(mock_task1, mock_task2))
    generator.generate(mock.sentinel.MODEL, '.')

    # tasks are called in correct order:
    assert mock_manager.mock_calls == [
        mock.call.task1.execute(mock.ANY),
        mock.call.task2.execute(mock.ANY)
    ]

    # check context content:
    context1 = mock_task1.execute.call_args[0][0]
    context2 = mock_task2.execute.call_args[0][0]
    assert context1 is context2, 'second context differrent'
    assert context2.generator == generator
    assert context2.outfolder == os.path.abspath('.')
    assert context2.model is mock.sentinel.MODEL
    assert context2.new_attribute == mock.sentinel.NEW_ATTRIBUTE


def test__task__executed_in_order():
    task = Task()

    task.elements = mock.Mock(return_value=iter((mock.sentinel.ELEM1, mock.sentinel.ELEM2,)))
    task.apply_to = mock.Mock()

    task.execute(mock.sentinel.CONTEXT)

    assert task.apply_to.mock_calls == [
        mock.call(mock.sentinel.ELEM1, mock.sentinel.CONTEXT),
        mock.call(mock.sentinel.ELEM2, mock.sentinel.CONTEXT),
    ]

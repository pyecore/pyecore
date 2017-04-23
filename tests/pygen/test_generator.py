import os
from unittest import mock

from pygen.generator import Generator


def test__generator__generate__no_tasks():
    # calling empty generator not raising anything:
    Generator(tasks=()).generate(mock.sentinel.MODEL, '.')


def test__generator__generate__tasks():
    mock_task1 = mock.MagicMock()
    mock_task2 = mock.MagicMock()

    mock_manager = mock.Mock()
    mock_manager.attach_mock(mock_task1, 'task1')
    mock_manager.attach_mock(mock_task2, 'task2')

    # let first task add some information to context:
    def execute(context):
        context.new_attribute = mock.sentinel.NEW_ATTRIBUTE

    mock_task1.execute = mock.MagicMock(side_effect=execute)

    g = Generator(tasks=(mock_task1, mock_task2))
    g.generate(mock.sentinel.MODEL, '.')

    # tasks are called in correct order:
    assert mock_manager.mock_calls == [
        mock.call.task1.execute(mock.ANY),
        mock.call.task2.execute(mock.ANY)
    ]

    # check context content:
    context1 = mock_task1.execute.call_args[0][0]
    context2 = mock_task2.execute.call_args[0][0]
    assert context1 is context2, 'second context differrent'
    assert context2.generator == g
    assert context2.outfolder == os.path.abspath('.')
    assert context2.model is mock.sentinel.MODEL
    assert context2.new_attribute == mock.sentinel.NEW_ATTRIBUTE

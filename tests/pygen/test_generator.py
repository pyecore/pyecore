import os
from unittest import mock

from pygen.generator import Generator, Task


def test__generator__generate__no_tasks():
    # calling empty generator not raising anything:
    Generator(tasks=()).generate(mock.sentinel.MODEL, '.')


def test__generator__generate__tasks():
    mock_task1 = mock.Mock()
    mock_task2 = mock.Mock()

    elements = mock.sentinel.ELEM1, mock.sentinel.ELEM2
    mock_task1.filtered_elements = mock.Mock(return_value=iter(elements))
    mock_task1.get_context = mock.Mock(return_value=mock.sentinel.CONTEXT1)
    mock_task2.filtered_elements = mock.Mock(return_value=iter(tuple()))
    mock_task2.get_context = mock.Mock(return_value=mock.sentinel.CONTEXT2)

    mock_manager = mock.Mock()
    mock_manager.attach_mock(mock_task1, 'task1')
    mock_manager.attach_mock(mock_task2, 'task2')

    generator = Generator(tasks=(mock_task1, mock_task2))
    generator.generate(mock.sentinel.MODEL, '.')

    outfolder = os.path.abspath('.')
    assert mock_manager.mock_calls == [
        mock.call.task1.filtered_elements(mock.sentinel.MODEL),
        mock.call.task1.get_context(
            generator=generator,
            outfolder=outfolder,
            model=mock.sentinel.MODEL,
            element=elements[0]
        ),
        mock.call.task1.execute(mock.sentinel.CONTEXT1),
        mock.call.task1.get_context(
            generator=generator,
            outfolder=outfolder,
            model=mock.sentinel.MODEL,
            element=elements[1]
        ),
        mock.call.task1.execute(mock.sentinel.CONTEXT1),
        mock.call.task2.filtered_elements(mock.sentinel.MODEL),
    ]


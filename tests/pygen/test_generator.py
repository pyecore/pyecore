import os
from unittest import mock

from pyecore.ecore import EModelElement
from pygen.generator import Generator, Task


def test__generator__generate__no_tasks():
    # calling empty generator not raising anything:
    Generator().generate(mock.sentinel.MODEL, mock.sentinel.OUTFOLDER)


def test__generator__generate__tasks():
    mock_task1 = mock.Mock()
    mock_task2 = mock.Mock()

    elements = mock.sentinel.ELEM1, mock.sentinel.ELEM2
    mock_task1.filtered_elements = mock.Mock(return_value=iter(elements))

    # no matching elements for this task:
    mock_task2.filtered_elements = mock.Mock(return_value=iter(tuple()))

    mock_manager = mock.Mock()
    mock_manager.attach_mock(mock_task1, 'task1')
    mock_manager.attach_mock(mock_task2, 'task2')

    generator = Generator()
    generator.tasks = (mock_task1, mock_task2)
    generator.generate(mock.sentinel.MODEL, mock.sentinel.FOLDERPATH)

    assert mock_manager.mock_calls == [
        mock.call.task1.filtered_elements(mock.sentinel.MODEL),
        mock.call.task1.run(mock.sentinel.ELEM1, mock.sentinel.FOLDERPATH),
        mock.call.task1.run(mock.sentinel.ELEM2, mock.sentinel.FOLDERPATH),
        mock.call.task2.filtered_elements(mock.sentinel.MODEL),
    ]


@mock.patch.object(Task, 'ensure_folder')
@mock.patch.object(Task, 'relative_path_for_element', return_value='file.ext')
@mock.patch.object(Task, 'generate_file')
def test__task__run(mock_generate_file, mock_relative_path_for_element, mock_ensure_folder):
    task = Task()
    task.run(mock.sentinel.ELEMENT, 'somefolder')

    outfile = os.path.join('somefolder', 'file.ext')
    mock_relative_path_for_element.assert_called_once_with(mock.sentinel.ELEMENT)
    mock_ensure_folder.assert_called_once_with(outfile)
    mock_generate_file.assert_called_once_with(mock.sentinel.ELEMENT, outfile)

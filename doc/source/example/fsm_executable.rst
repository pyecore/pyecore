.. _FSM:

Executable Model Example: Fine State Machine
============================================

As an example, this description re-implements the Finite State Machine (FSM) example as
described in the `ALE tutorial page <http://gemoc.org/ale-lang/tutorial.html>`_.
ALE is a domain specific language designed for EMF Java that provides (_extracted
from the ALE homepage_):

- Metamodel extension: The very same mechanism can be used to extend existing
  Ecore metamodels and insert new features (eg. attributes) in a non-intrusive
  way
- Executable metamodeling: Re-open existing EClasses to insert new methods
  with their implementations
- Interpreted: Just run the behavior on a model directly in your modeling environment
- Extensible: If ALE doesn’t fit your needs, register classes as services
  and invoke them inside your implementations of EOperations.

PyEcore provides the exact same capability to use ALE in a Python environment.
You can find more information about how to add behavior to your metamodel in the
":ref:`behavior`" section of the advanced User Documentation.

The following gives you the full code for the FSM example of the ALE
tutorial page, but in a pure Python style using PyEcore. The script:

- opens the FSM Ecore metamodel from a remote location
- registers the FSM Ecore metamodel in the metamodel registry
- defines additional behavior for each metaclass from the FSM Ecore metamodel
- defines an entry point
- opens a FSM XMI model from a remote location
- executes the loaded metamodel

.. code-block:: python

    from pyecore.resources.resource import HttpURI, ResourceSet
    from pyecore.utils import DynamicEPackage
    from pyecore.ecore import EcoreUtils
    import pyecore.behavior as behavior

    # Load metamodel
    rset = ResourceSet()
    uri = HttpURI('https://raw.githubusercontent.com/gemoc/ale-lang/master/'
                  'examples/minifsm/model/MiniFsm.ecore')
    package_root = rset.get_resource(uri).contents[0]
    rset.metamodel_registry[package_root.nsURI] = package_root

    fsm = DynamicEPackage(package_root)


    # Code for each overridden/added method
    @fsm.Transition.behavior
    def is_activated(self):
        return (self.fsm.currentEvent == self.event
                and self.incoming == self.fsm.currentState)


    @fsm.State.behavior
    def execute(self):
        print('Execute', self.name)


    @fsm.FSM.behavior
    def handle(self, event):
        print('Handle', event)
        self.currentEvent = event
        self.currentState = [t for t in self.transitions
                             if t.is_activated()][0].outgoing


    @fsm.FSM.behavior
    @behavior.main
    def entry_point(self):
        print('Start')
        events = ['event1', 'event2']

        self.currentState = [s for s in self.states
                             if isinstance(s, fsm.Initial)][0]
        self.currentState.execute()

        for event in events:
            self.handle(event)
            self.currentState.execute()

        print('End')


    # Load the model
    uri = HttpURI('https://raw.githubusercontent.com/gemoc/ale-lang/master/'
                  'examples/minifsm/model/FSM.xmi')
    resource = rset.get_resource(uri)
    root = resource.contents[0]

    # Execute the model
    behavior.run(root)

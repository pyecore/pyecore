from .{{ element.name }} import getEClassifier, eClassifiers
from .{{ element.name }} import name, nsURI, nsPrefix, eClass
from .{{ element.name }} import {{ element.eClassifiers | join(', ', attribute='name') }}

{% if not element.eSuperPackage %}
    {% with %}
        {% set containing_types = element | all_contents(ecore.EClassifier) | map(attribute='eContainingClass') | list %}
        {% set referenced_types = element | all_contents(ecore.EReference) | map(attribute='eType') | list %}
        {% set types = containing_types + referenced_types %}
        {% for sub in element | all_contents(ecore.EPackage) %}
from {{ sub | pyfqn }} import {{ types | selectattr('ePackage', sub) | join(', ') }}
        {% endfor %}
    {% endwith %}
{% endif %}

from .{{ element.name }} import getEClassifier, eClassifiers
from .{{ element.name }} import name, nsURI, nsPrefix, eClass
from .{{ element.name }} import {{ element.eClassifiers | join(', ', attribute='name') }}

{%- if not element.eSuperPackage %}
    {%- with %}
        {%- set containing_types = element | all_contents(ecore.EClassifier) | map(attribute='eContainingClass') | list %}
        {%- set referenced_types = element | all_contents(ecore.EReference) | map(attribute='eType') | list %}
        {%- set types = containing_types + referenced_types %}
        {%- for sub in element | all_contents(ecore.EPackage) %}
from {{ sub | pyfqn }} import {{ types | selectattr('ePackage', sub) | join(', ') }}
        {% endfor -%}
    {% endwith -%}
{% endif %}
from . import {{ element.name }}

{%- if element.eSuperPackage %}
from .. import {{ element.eSuperPackage.name }}
{% endif %}

{%- for sub in element.eSubpackages %}
from . import {{ sub.name }}
{% endfor %}

__all__ = [{{ element.eClassifiers | map(attribute='name') | map('pyquotesingle') | join(', ') }}]

eSubpackages = [{{ element.eSubpackages | map(attribute='name') | join(', ') }}]
eSuperPackage = {{ element.eSuperPackage.name | default('None') }}
{% if not element.eSuperPackage %}
    {%- for e in element | all_contents(ecore.EReference) | rejectattr('eOpposite') %}
{{ e.eContainingClass.name }}.{{ e.name }}.eType = {{ e.eType.name }}
    {%- endfor %}
    {%- with opposites = element | all_contents(ecore.EReference) | selectattr('eOpposite') | list %}
        {%- for e in opposites %}
{{ e.eContainingClass.name }}.{{ e.name }}.eType = {{ e.eType.name }}
            {%- if e is opposite_before_self(opposites) %}
{{ e.eContainingClass.name }}.{{ e.name }}.eOpposite = {{ e.eOpposite.eContainingClass.name }}.{{ e.eOpposite.name }}
            {%- endif %}
        {%- endfor %}
    {%- endwith %}
{%- endif %}

"""Definition of meta model '{{ element.name }}'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *
{% for c in imported_classifiers %}
    from {{ c.ePackage.qualifiedName }} import {{ c.name }}
{% endfor %}

name = '{{ element.name }}'
nsURI = '{{ element.nsURI }}'
nsPrefix = '{{ element.nsPrefix }}'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_enum(e) %}
{{ e.name }} = EEnum('{{ e.name }}', literals=[{{ e.eLiterals | map(attribute='name') | map('pyquotesingle') | join(', ') }}])  # noqa
{% endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_class_header(c) -%}
class {{ c.name }}({{ c | supertypes }}):
    {%- with doc = c | documentation -%}
        {% if doc %}
    """{{ doc }}"""
        {%- endif %}
    {%- endwith -%}
{% endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_attribute(a) -%}
    _{{ a.name }} = EAttribute({% if a.derived %}name='{{ a.name }}', {% endif %}eType={{ a.eType.name }}{% if a.many %}, upper=-1{% endif %}{% if a.derived %}, derived=True{% endif %}{% if not a.changeable %}, changeable=False{% endif %})
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_class(c) %}

{% if c.abstract %}@abstract
{% endif -%}
{{ generate_class_header(c) -}}
{% for a in c.eAttributes %}
    {{ generate_attribute(a) -}}
{% endfor %}
    # TODO OTHER CLASS CONTENT
{% endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- for c in element.eClassifiers if c is type(ecore.EEnum) %}
{{ generate_enum(c) }}
{%- endfor %}

{%- for c in classes -%}
{{ generate_class(c) }}
{%- endfor %}

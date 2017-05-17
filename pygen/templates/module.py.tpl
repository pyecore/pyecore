"""Definition of meta model '{{ element.name }}'."""
from functools import partial
import pyecore.ecore as Ecore
from pyecore.ecore import *
{% for c in imported_classifiers -%}
    from {{ c.ePackage | pyfqn }} import {{ c.name }}
{% endfor %}

name = '{{ element.name }}'
nsURI = '{{ element.nsURI | default(boolean=True) }}'
nsPrefix = '{{ element.nsPrefix | default(boolean=True) }}'

eClass = EPackage(name=name, nsURI=nsURI, nsPrefix=nsPrefix)

eClassifiers = {}
getEClassifier = partial(Ecore.getEClassifier, searchspace=eClassifiers)

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_enum(e) %}
{{ e.name }} = EEnum('{{ e.name }}', literals=[{{ e.eLiterals | map(attribute='name') | map('pyquotesingle') | join(', ') }}])
{% endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_class_header(c) -%}
class {{ c.name }}({{ c | supertypes }}):
    {{ c | docstringline -}}
{% endmacro -%}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_attribute(a) -%}
    {% if a.derived %}_{% endif -%}
    {{ a.name }} = EAttribute(
        {%- if a.derived %}name='{{ a.name }}', {% endif -%}
        eType={{ a.eType.name }}
        {%- if a.many %}, upper=-1{% endif %}
        {%- if a.derived %}, derived=True{% endif %}
        {%- if not a.changeable %}, changeable=False{% endif -%}
    )
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_reference(r) -%}
    {{ r.name }} = EReference({{ r | refqualifiers }})
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_derived_attribute(d) -%}
    @property
    def {{ d.name }}(self):
        return self._{{ d.name }}

    @{{ d.name }}.setter
    def {{ d.name }}(self, value):
        self._{{ d.name }} = value
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_class_init_args(c) -%}
    {% if c.eStructuralFeatures %}, *, {% endif -%}
    {{ c.eStructuralFeatures | map(attribute='name') | map('re_sub', '$', '=None') | join(', ') }}
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_feature_init(feature) %}
    {%- if feature.upperBound == 1 %}
        if {{ feature.name }} is not None:
            self.{{ feature.name }} = {{ feature.name }}
    {%- else %}
        if {{ feature.name }}:
            self.{{ feature.name }}.extend({{ feature.name }})
    {%- endif %}
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_class_init(c) %}
    def __init__(self{{ generate_class_init_args(c) }}, **kwargs):
    {%- if not c.eSuperTypes %}
        if kwargs:
            raise AttributeError('unexpected arguments: {}'.format(kwargs))
    {%- endif %}

        super().__init__({% if c.eSuperTypes %}**kwargs{% endif %})
    {%- for feature in c.eStructuralFeatures | reject('type', ecore.EReference) %}
    {{ generate_feature_init(feature) }}
    {%- endfor %}
    {%- for feature in c.eStructuralFeatures | select('type', ecore.EReference) %}
    {{ generate_feature_init(feature) }}
    {%- endfor %}
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_operation_args(o) -%}
    {% if o.eParameters %}, {% endif -%}
    {{ o.eParameters | join(', ', attribute='name') }}
{%- endmacro  %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_operation(o) %}
    def {{ o.name }}(self{{ generate_operation_args(o) }}):
        {{ o | docstringline -}}
        raise NotImplementedError('operation {{ o.name }}(...) not yet implemented')
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- macro generate_class(c) %}

{% if c.abstract %}@abstract
{% endif -%}
{{ generate_class_header(c) }}
{%- for a in c.eAttributes %}
    {{ generate_attribute(a) -}}
{% endfor %}
{%- for r in c.eReferences %}
    {{ generate_reference(r) -}}
{% endfor %}
{% for d in c.eAttributes | selectattr('derived')  %}
    {{ generate_derived_attribute(d) }}
{% endfor %}
{{- generate_class_init(c) }}
{% for o in c.eOperations %}
    {{ generate_operation(o) }}
{% endfor %}
{%- endmacro %}

{#- -------------------------------------------------------------------------------------------- -#}

{%- for c in element.eClassifiers if c is type(ecore.EEnum) %}
{{ generate_enum(c) }}
{%- endfor %}

{%- for c in classes -%}
{{ generate_class(c) }}
{%- endfor %}

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

{% for c in element.eClassifiers if c is type(ecore.EEnum) %}
c.generate()
{% endfor %}


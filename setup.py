import os
from setuptools import find_packages, setup

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

bower_json = {
    "dependencies": {
        "jquery": "^3.2.1",
        "bootstrap": "^3.3.7",
        "bootstrap-multiselect": "^0.9.13",
        "bootstrap-datepicker": "^1.7.0",
        "jquery-tablesort": "^0.0.11",
        "leaflet": "^1.1.0",
        "tooltipster": "^4.2.5",
        "leaflet.markercluster": "Leaflet.markercluster#^1.0.6",
      },
    "resolutions": {
        "jquery": "1.9.1 - 3"
      }
}

setup(
    name='apis-core',
    version='0.9.6',
    packages=find_packages(),
    include_package_data=True,
    license='MIT License',  # example license
    description='APIS core package. Includes entities, relations, vocabularies,\
    labels and the helper scripts for RDF parsing.',
    long_description=README,
    url='https://www.apis.acdh.oeaw.ac.at/',
    author='Matthias Schlögl, Peter Andorfer',
    author_email='matthias.schloegl@oeaw.ac.at, peter.andorfer@oeaw.ac.at',
    classifiers=[
        'Environment :: Web Environment',
        'Framework :: Django',
        'Framework :: Django :: 2.0',  # replace "X.Y" as appropriate
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',  # example license
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
    ],
    install_requires=[
        'calmjs.bower',
        'Django>=2.0',
        'django-autocomplete-light>=3.2.10',
        'django-crispy-forms>=1.7.0',
        'django-filter>=1.1.0',
        'django-gm2m>=0.6.1',
        'django-guardian>=1.4.9',
        'django-model-utils>=3.1.2',
        'django-reversion>=2.0.13',
        'django-reversion-compare>=0.8.4',
        'django-tables2>=1.21.1',
        'djangorestframework>=3.7.7',
        'djangorestframework-csv>=2.1.0',
        'djangorestframework-xml>=1.3.0',
        'lxml>=4.2.4',
        'python-dateutil>=2.7.0',
        'rdflib>=4.2.2',
        'requests>=2.18.4',
    ],
    bower_json=bower_json,
)

from setuptools import setup

setup(
    name='inception_fishing',
    version='0.2.0',
    description='Corpus-Document-Annotation NLP utility data-structures with import-export facilities to: entity-fishing, inception, clef-HIPE 2020 scorer and spacy.',
    url='https://github.com/dddpt/inception-fishing',
    author='Didier Dupertuis',
    license='Apache License 2.0',
    packages=['inception_fishing'],
    install_requires=[
        'requests>=2.22.0',
        'lxml>=4.5.0',
        'pandas>=1.3.3',
        'spacy==3.2.0'
    ],
    setup_requires=['wheel'],
    classifiers=[
        'Intended Audience :: Science/Research',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9'
    ],
)

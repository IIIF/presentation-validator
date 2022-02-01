"""Setup for iiif/presentation-validator."""
from setuptools import setup, Command
import os
import re

class Coverage(Command):
    """Class to allow coverage run from setup."""

    description = "run coverage"
    user_options = []

    def initialize_options(self):
        """Empty initialize_options."""
        pass

    def finalize_options(self):
        """Empty finalize_options."""
        pass

    def run(self):
        """Run coverage program."""
        os.system("coverage run --omit=tests/*,setup.py setup.py test")
        os.system("coverage report")
        os.system("coverage html")
        print("See htmlcov/index.html for details.")

setup(
    name='iiif-presentation-validator',
    version='0.0.3',
    scripts=['iiif-presentation-validator.py'],
    classifiers=["Development Status :: 4 - Beta",
                 "Intended Audience :: Developers",
                 "Operating System :: OS Independent",
                 "Programming Language :: Python",
                 "Programming Language :: Python :: 3.7",
                 "Programming Language :: Python :: 3.8",
                 "Programming Language :: Python :: 3.9",
                 "Topic :: Internet :: WWW/HTTP",
                 "Topic :: Multimedia :: Graphics :: Graphics Conversion",
                 "Topic :: Software Development :: "
                 "Libraries :: Python Modules",
                 "Environment :: Web Environment"],
    url='https://github.com/IIIF/presentation-validator',
    description='Validator for the IIIF Presentation API',
    long_description=open('README.md').read(),
    install_requires=[
        'bottle>=0.12.9',
        'iiif_prezi>=0.2.2',
        'jsonschema',
        'jsonpath_rw',
        'requests'
    ],
    extras_require={
        ':python_version>="3.6"': ["Pillow>=3.2.0"],
    },
    test_suite="tests",
    tests_require=[
        "coverage",
        "mock",
    ],
    cmdclass={
        'coverage': Coverage,
    },
)

# http://bugs.python.org/issue15881#msg170215
from setuptools import find_packages, setup

setup(
    name="biomaj2galaxy",
    version='2.2.0',
    description="Command-line utility to assist in interconnecting BioMAJ (https://biomaj.genouest.org/) with Galaxy (http://galaxyproject.org/).",
    author="Anthony Bretaudeau",
    author_email="anthony.bretaudeau@inra.fr",
    url="https://github.com/genouest/biomaj2galaxy",
    install_requires=['future', 'bioblend', 'click'],
    packages=find_packages(),
    license='MIT',
    platforms="Posix; MacOS X; Windows",
    entry_points='''
        [console_scripts]
        biomaj2galaxy=biomaj2galaxy.cli:biomaj2galaxy
    ''',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Scientific/Engineering",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
    ])

"""Setup for local MkDocs plugins."""

from setuptools import setup, find_packages

setup(
    name='mkdocs-plugins-local',
    version='0.1.0',
    description='Local MkDocs plugins for Universal Smart Lighting Control documentation',
    packages=find_packages(),
    install_requires=[
        'mkdocs>=1.5.0',
        'PyYAML>=6.0',
    ],
    entry_points={
        'mkdocs.plugins': [
            'auto_toc = mkdocs_plugins.auto_toc:AutoTocPlugin',
        ]
    }
)

from setuptools import setup

setup(
    name='pyChanga',
    version='1.0.0',
    description='pyChanga: Python music on one shared clock',
    packages=['pyChanga'],
    package_dir={'pyChanga': '../../pyChanga_package/pyChanga'},
    python_requires='>=3.11',
    install_requires=[],
    include_package_data=True,
    package_data={
        'pyChanga': ['sounds/TimGM6mb.sf2', 'sounds/*.txt', 'sounds/*.json'],
    },
)

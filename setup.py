from setuptools import setup

long_desc = open('README.md').read()

setup(
    name='anosql',
    version='0.0.2',
    url='https://github.com/honza/anosql',
    install_requires=[],
    description='Easy SQL in Python',
    long_description=long_desc,
    author='Honza Pokorny',
    author_email='me@honza.ca',
    maintainer='Honza Pokorny',
    maintainer_email='me@honza.ca',
    packages=['anosql'],
    include_package_data=True
)

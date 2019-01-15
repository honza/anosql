from setuptools import setup, find_packages

with open('README.rst') as readme_file:
    long_desc = readme_file.read()

setup(
    name='anosql',
    version='1.0.1',
    url='https://github.com/honza/anosql',
    install_requires=[],
    description='Easy SQL in Python',
    long_description=long_desc,
    author='Honza Pokorny',
    author_email='me@honza.ca',
    maintainer='Honza Pokorny',
    maintainer_email='me@honza.ca',
    packages=find_packages(),
    include_package_data=True
)

from setuptools import setup


setup(
    name='workqueue',
    version="0.1",
    author="Adam Mesha",
    packages=['workqueue', 'queueworker'],
    package_dir={'': 'src'},
)

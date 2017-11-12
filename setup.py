from setuptools import setup, find_packages

install_requirements = [
    'kubernetes==3.*',
    'tornado',
    'traitlets',
    'docker',
    'jinja2',
    'prometheus_client'
]

setup_requirements = [
    'pytest-runner'
]

test_requirements = [
    'pytest'
]

setup(
    name='binderhub',
    version='0.1.1',
    install_requires=install_requirements,
    python_requires='>=3.5',
    author='Project Jupyter Contributors',
    author_email='jupyter@googlegroups.com',
    license='BSD',
    packages=find_packages(),
    include_package_data=True,
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements
)

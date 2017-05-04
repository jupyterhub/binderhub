from setuptools import setup, find_packages

setup(
    name='iamsoscaredtonamethis',
    version='0.1',
    install_requires=[
        'kubernetes==1.*',
        'tornado'
    ],
    author='Yuvi Panda',
    author_email='yuvipanda@gmail.com',
    license='BSD',
    packages=find_packages(),
)

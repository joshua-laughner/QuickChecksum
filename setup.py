from setuptools import setup

setup(
    name='QuickChecksum',
    version='1.0.0',
    packages=['quickchecksum'],
    url='https://github.com/joshua-laughner/QuickChecksum',
    license='GNU GPLv3',
    author='Joshua Laughner',
    author_email='jllacct119@gmail.com',
    description='A small command line utility to verify a checksum for one file',
    entry_points={'console_scripts': ['qcsum=quickchecksum.__main__:main']}
)

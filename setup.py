# -*- coding: utf-8 -*-
import setuptools
from os.path import join, dirname

from setuptools.command.test import test as TestCommand
import sys

VERSION = (0, 7)

class Tox(TestCommand):

    user_options = TestCommand.user_options + [
        ('environment=', 'e', "Run 'test_suite' in specified environment")
    ]
    environment = None

    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        #import here, cause outside the eggs aren't loaded
        import tox
        if self.environment:
            self.test_args.append('-e{0}'.format(self.environment))
        errno = tox.cmdline(self.test_args)
        sys.exit(errno)

setuptools.setup(
    name='python-cielo',
    version='.'.join(map(str, VERSION)),
    description='python-cielo is a lightweight lib for making payments over the Cielo webservice (Brazil)',
    long_description=open(join(dirname(__file__), "README.rst")).read(),
    classifiers=[
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    keywords='cielo e-commerce',
    author='Renato Pedigoni',
    author_email='renatopedigoni@gmail.com',
    url='http://github.com/rpedigoni/python-cielo',
    license='BSD',
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['requests==1.2.3', 'xmltodict==0.8.1'],
    tests_require=['vcrpy==0.3.3', 'freezegun==0.1.8', 'tox>=1.6.1', 'virtualenv>=1.11.2'],
    test_suite='cielo.tests',
    cmdclass = {'test': Tox},
)

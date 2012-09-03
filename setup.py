# encoding: utf-8
from setuptools import setup, find_packages

setup(
    name = 'au-skema',
    version = "0.1-dev01",
    description = '',
    author = u'Kristian Øllegaard',
    author_email = 'kristian@oellegaard.com',
    zip_safe=False,
    include_package_data = True,
    py_modules=['skema'],
    install_requires=[
        open("requirements.txt").readlines(),
    ],
    entry_points={
        'console_scripts': [
            'skema = skema:main',
            ]
    },
)
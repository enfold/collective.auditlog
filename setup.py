# coding=utf-8
from setuptools import find_packages
from setuptools import setup
import os

version = '1.3.7.dev0'

setup(
    name='collective.auditlog',
    version=version,
    description=(
        "Provides extra conditions and triggers for all content "
        "actions"
    ),
    long_description="%s\n%s" % (
        open("README.rst").read(),
        open(os.path.join("docs", "HISTORY.rst")).read(),
    ),
    # Get more strings from
    # http://pypi.python.org/pypi?:action=list_classifiers
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Development Status :: 5 - Production/Stable",
    ],
    keywords='Plone Audit Log',
    author='rain2o',
    author_email='Joel@rain2odesigns.com',
    url='http://svn.plone.org/svn/collective/',
    license='GPL',
    packages=find_packages(exclude=['ez_setup']),
    namespace_packages=['collective'],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'setuptools',
        'sqlalchemy>=1.4',
        'five.globalrequest',
        'five.formlib',  # plone 5
        'plone.app.iterate',
        'plone.registry',
        'Products.CMFCore',
        'six',
    ],
    extras_require={
        'async': [
            'plone.app.async',
        ],
        'celery': [
            'collective.celery',
        ],
        'test': [
            'plone.app.testing',
        ]
    },
    entry_points="""
      # -*- Entry points: -*-

      [z3c.autoinclude.plugin]
      target = plone

      [celery_tasks]
      audit = collective.auditlog.tasks
      """
)

import os
import fnmatch
from setuptools import find_packages
from setuptools import setup

version = '0.0.1'

here = os.path.abspath(os.path.dirname(__file__))
try:
    README = open(os.path.join(here, 'README.md')).read()
except IOError:
    README = ''

def find_data_files(dir, pat):
    files = []
    for f in os.listdir(dir):
        if fnmatch.fnmatch(f, pat):
            files.append(os.path.join(dir, f))
    return (dir, files)

install_requires = [
    'numpy',
    'Pillow',
    'scikit-image',
    'click',
    'flask'
]

tests_require = [
]

dextr_require = [
    'dextr'
]

include_package_data = True
data_files = [
    ('fastlabel/templates', [
        'fastlabel/templates/labeller_page.jinja2'
    ]),
    ('fastlabel/templates/inline', [
        'fastlabel/templates/inline/labeller_app.html',
        'fastlabel/templates/inline/image_labeller.html',
        'fastlabel/templates/inline/image_labeller_css.html',
        'fastlabel/templates/inline/image_labeller_scripts.html',
    ]),
    find_data_files('fastlabel/static', '*.*'),
    find_data_files('fastlabel/static/open-iconic/css', '*.*'),
    find_data_files('fastlabel/static/open-iconic/fonts', '*.*'),
    find_data_files('fastlabel/static/labelling_tool', '*.*'),
]

setup(
    name="fastlabel",
    version=version,
    description="An image labelling tool for creating segmentation data sets made with Flask.",
    long_description="\n\n".join([README]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.6",
        "Topic :: Software Development :: User Interfaces",
    ],
    keywords="",
    author="Thomas Capelle",
    # author_email="brittix1023 at gmail dot com",
    url="https://github.com/tcapelle/fastlabel",
    license="MIT",
    packages=find_packages(),
    include_package_data=include_package_data,
    data_files=data_files,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={
        'testing': tests_require,
        'dextr': dextr_require,
    },
)

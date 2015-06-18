from setuptools import setup, find_packages
import functools
import os
import platform

_PYTHON_VERSION = platform.python_version()
_in_same_dir = functools.partial(os.path.join, os.path.dirname(__file__))

with open(_in_same_dir("chords", "__version__.py")) as version_file:
    exec(version_file.read())  # pylint: disable=W0122

install_requires = [
    # DO NOT ADD pyforge, lxml or any other package only required for testing
]

if _PYTHON_VERSION < "2.7":
    pass

if _PYTHON_VERSION < "3.3":
    pass

setup(name="chords",
      classifiers=[
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3.4",
      ],
      description="Simple task and resource management",
      license="MIT",
      author="Omer Gertel",
      author_email="omer.gertel@gmail.com",
      url="http://omergertel.github.io/chords",
      version=__version__,  # pylint: disable=E0602
      packages=find_packages(exclude=["tests"]),
      install_requires=install_requires,
)

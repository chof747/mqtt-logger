from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="mqtt-logger",
    version="0.0.4",
    author="Christian Hofbauer",
    author_email="chof@gmx.at",
    description="lightweight python module that can be used to log messages to mqtt",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/your-repo",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.11',
    install_requires=[
      'paho-mqtt==2.1.0'
    ],
    test_suite='tests',
)
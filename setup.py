from setuptools import find_packages, setup


setup(
    name="doctobil",
    version="0.0.13",
    author="Mathias Gout",
    packages=find_packages(exclude=["tests"]),
    install_requires=["selenium==4.12.0", "beautifulsoup4==4.12.2"],
    python_requires="==3.9.*",
)

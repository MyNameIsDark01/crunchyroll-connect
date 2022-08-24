import setuptools

setuptools.setup(
    name="crunchyroll_connect",
    version="1.4.9",
    author="mynameisdark01",
    description="API for Crunchyroll BETA",
    url="https://github.com/MyNameIsDark01/crunchyroll-connect",
    project_urls={
        "Tracker": "https://github.com/MyNameIsDark01/crunchyroll-connect/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "requests",
    ],
    packages=setuptools.find_packages(),
    python_requires=">=3.6",
)
import setuptools


setuptools.setup(
    name="verydisco",
    version="0.1",
    description="Create APIs from a Google service discovery document",
    author="David Buxton",
    packages=setuptools.find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "pydantic",
    ],
    classifiers=[
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Topic :: Internet :: WWW/HTTP",
    ],
)

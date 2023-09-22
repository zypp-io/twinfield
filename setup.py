from setuptools import find_packages, setup

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as fp:
    install_requires = fp.read()

setup(
    name="twinfield",
    version="2.1.2",
    author="Zypp",
    author_email="hello@zypp.io",
    description="Read and insert data using the Twinfield API.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    keywords="python, twinfield, API",
    url="https://github.com/zypp-io/twinfield",
    packages=find_packages(),
    install_requires=install_requires,
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    project_urls={
        "Bug Reports": "https://github.com/zypp-io/twinfield/issues",
        "Source": "https://github.com/zypp-io/twinfield",
    },
)

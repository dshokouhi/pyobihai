import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pyobihai",
    version="1.2.3",
    author="Daniel Shokouhi",
    author_email="dshokouhi@gmail.com",
    description="A Python wrapper for Obihai",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dshokouhi/pyobihai",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)

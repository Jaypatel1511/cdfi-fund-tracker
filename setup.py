from setuptools import setup, find_packages

setup(
    name="cdfi-fund-tracker",
    version="0.2.0",
    description="CDFI Fund award analysis & compliance tracking — CDFI Program, BEA, NACA, Native American, RAPID, CMF, and Bond Guarantee awards. BRING YOUR OWN DATA: no CDFI Fund ingestion path is implemented; sample data is synthetic. See README.",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Jay Patel",
    author_email="thejaypatel1511@gmail.com",
    url="https://github.com/Jaypatel1511/cdfi-fund-tracker",
    license="MIT",
    packages=find_packages(exclude=["tests*"]),
    python_requires=">=3.9",
    install_requires=[],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial",
    ],
)

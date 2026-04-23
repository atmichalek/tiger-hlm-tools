from setuptools import setup, find_packages

setup(
    name="tiger_hlm_setup",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "numpy",
        "pandas",
        "xarray",
        "scipy",
    ],
)

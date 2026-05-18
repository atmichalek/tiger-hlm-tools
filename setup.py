from setuptools import setup, find_packages

setup(
    name="tiger_hlm_setup",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "tiger_hlm_setup": ["templates/**/*", "templates/*"],
    },
    install_requires=[
        "numpy",
        "pandas",
        "xarray",
        "scipy",
    ],
)
from setuptools import setup, find_packages

setup(
    name="browse_code",
    version="0.1.3",
    description="A local AI bridge package",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "browse_code": ["extension/*"],
    },
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic"
    ],
    entry_points={
        "console_scripts": [
            "bc=browse_code.cli:main",
        ],
    },
)

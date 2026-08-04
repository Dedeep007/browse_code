from setuptools import setup, find_packages

setup(
    name="browse_code",
    version="0.2.79",
    description="Turn any AI chatbot into an autonomous coding agent",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "browse_code": ["extension_chrome/*", "extension_firefox/*"],
    },
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "rich",
    ],
    entry_points={
        "console_scripts": [
            "bc=browse_code.cli:main",
        ],
    },
)

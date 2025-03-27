from setuptools import setup, find_packages

setup(
    name="router",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "grpcio",
        "protobuf",
        "openai",
        "langchain",
        "crewai",
    ],
    python_requires=">=3.8",
) 
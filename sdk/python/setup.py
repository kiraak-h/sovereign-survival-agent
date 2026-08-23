from setuptools import setup, find_packages

setup(
    name="sovereign-oracle",
    version="1.0.0",
    description="Machine-to-Machine (M2M) Security Oracle SDK for Autonomous Web3 Trading Bots",
    long_description=open("README.md").read() if open("README.md") else "",
    long_description_content_type="text/markdown",
    author="Sovereign Survival Agent",
    packages=find_packages(),
    install_requires=[
        "requests>=2.25.1",
        "eth-account>=0.8.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)

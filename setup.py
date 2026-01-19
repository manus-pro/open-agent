from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = fh.read().splitlines()

setup(
    name="open-agent",
    version="0.1.0",
    author="Xinyu Zhang",
    author_email="example@example.com",
    description="A modular framework for autonomous multi-tool agent orchestration with memory-enabled planning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/manus-pro/open-agent",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "open-agent=main:main",
            "open-agent-flow=run_flow:main",
        ],
    },
)

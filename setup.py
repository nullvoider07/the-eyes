from setuptools import setup, find_packages

# Setup configuration for the eye-capture package
setup(
    name="eye-capture",
    version="0.2.1",
    description="AI-native vision capture tool for CUA workflows",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "click>=8.1.7",
        "pyyaml>=6.0.1",
        "requests>=2.31.0",
    ],
    entry_points={
        'console_scripts': [
            'eye=eye.cli:main',
        ],
    },
    python_requires=">=3.11",
)
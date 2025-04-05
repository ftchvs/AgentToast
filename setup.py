"""Setup script for AgentToast."""
from setuptools import find_packages, setup

setup(
    name="agenttoast",
    version="0.1.0",
    description="AI-driven personalized news audio digest service",
    author="Your Name",
    author_email="your.email@example.com",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        line.strip()
        for line in open("requirements.txt")
        if line.strip() and not line.startswith("#")
    ],
    entry_points={
        "console_scripts": [
            "agenttoast=agenttoast.api.main:app",
        ],
    },
) 
#!/usr/bin/env python3
"""
Configuration d'installation pour l'application ACFC.

Ce fichier permet d'installer l'application ACFC en mode développement
pour résoudre les problèmes d'import dans les tests et en CI/CD.

Usage :
    pip install -e .
"""

from setuptools import setup, find_packages

setup(
    name="acfc",
    version="1.0.0",
    description="Application ACFC - Gestion de clients et commandes",
    author="ACFC Development Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.0.0",
        "SQLAlchemy>=1.4.0",
        "mysql-connector-python>=8.0.0",
        "pymongo>=4.0.0",
        "argon2-cffi>=21.0.0",
        "Flask-Session>=0.4.0",
        "Werkzeug>=2.0.0",
    ],
    extras_require={
        "test": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "pytest-flask>=1.2.0",
            "pytest-mock>=3.10.0",
            "coverage>=6.0.0",
        ],
        "dev": [
            "flake8>=5.0.0",
            "black>=22.0.0",
            "mypy>=1.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)

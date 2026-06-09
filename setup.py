from setuptools import find_packages, setup

setup(
    name="iserv-ausleihe-api",
    version="0.1.0",
    description="Inoffizieller Python-Client für die IServ Schulbuchausleihe REST API",
    author="Niklas",
    python_requires=">=3.9",
    packages=find_packages(),
    install_requires=[
        "requests>=2.31.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        # Excel-Bestands-/Nachbestellungs-Tooling
        "bestand": ["openpyxl>=3.1.0"],
        # Entwicklung / Tests
        "dev": ["pytest>=7.0"],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
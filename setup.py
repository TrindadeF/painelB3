from setuptools import setup, find_packages

setup(
    name="brazil-stocks-dashboard",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "matplotlib",
        "pandas_market_calendars",
        "numpy",
    ],
    entry_points={
        "console_scripts": [
            "brazil-stocks-dashboard=src.main:main",
        ],
    },
)
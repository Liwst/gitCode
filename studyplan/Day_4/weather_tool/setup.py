from setuptools import setup, find_packages

setup(
    name="weather_tool",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "requests>=2.25",
        "python-dateutil>=2.8"
    ],
    entry_points={
        "console_scripts": [
            "weather=weather.cli:main"
        ]
    },
    python_requires=">=3.8"
)

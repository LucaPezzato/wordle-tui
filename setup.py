from setuptools import find_packages, setup

setup(
    name="wordle-tui",
    version="0.1.0",
    packages=find_packages(),
    package_data={
        "wordle_tui": ["data/*.json.gz"],
    },
    include_package_data=True,
    install_requires=[
        "textual>=0.80.0",
        "rich>=13.0.0",
    ],
    entry_points={
        "console_scripts": [
            "wordle-tui=wordle_tui.cli:main",
        ],
    },
)

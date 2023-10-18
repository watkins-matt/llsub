from setuptools import find_packages, setup

setup(
    name="llsub",
    version="0.1",
    packages=find_packages(),
    install_requires=["pysubs2", "deep_translator", "tqdm"],
    entry_points={
        "console_scripts": [
            "llsub=llsub.llsub:main",
        ],
    },
)

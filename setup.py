from setuptools import setup
import os

VERSION = "0.1"


def get_long_description():
    with open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "README.md"),
        encoding="utf8",
    ) as fp:
        return fp.read()


setup(
    name="surveillance-analysis",
    description="null",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    author="John Wiseman",
    url="https://github.com/wiseman/surveillance-analysis",
    project_urls={
        "Issues": "https://github.com/wiseman/surveillance-analysis/issues",
        "CI": "https://github.com/wiseman/surveillance-analysis/actions",
        "Changelog": "https://github.com/wiseman/surveillance-analysis/releases",
    },
    license="Apache License, Version 2.0",
    version=VERSION,
    packages=["surveillance_analysis"],
    entry_points="""
        [console_scripts]
        surveillance-analysis=surveillance_analysis.cli:cli
    """,
    install_requires=["click", "ffmpeg-python", "tqdm", "webrtcvad"],
    extras_require={
        "test": ["pytest"]
    },
    tests_require=["surveillance-analysis[test]"],
    python_requires=">=3.6",
)

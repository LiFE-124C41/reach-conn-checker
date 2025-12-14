
from setuptools import setup, find_packages

setup(
    name="reach-conn-checker",
    version="1.0.0",
    description="Network Reachability & Connection Stability Checker",
    author="System Administrator",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "reach-conn-checker=reach_conn_checker.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Networking :: Monitoring",
    ],
    install_requires=[
        "windows-curses; platform_system=='Windows'",
    ],
)

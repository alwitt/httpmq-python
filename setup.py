from setuptools import find_packages, setup

setup(
    name="httpmq",
    version="0.1.0",
    description="HTTP MQ Python client module",
    author="Rhine Cliff",
    author_email="rhinecliff@protonmail.com",
    packages=find_packages(exclude=["test", "scripts"]),
    scripts=["scripts/httpmq_test_cli.py"],
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "aiohttp",
        "aiostream",
        "asyncio",
        "python-dateutil",
    ],
    setup_requires=["black", "flake8", "pylint", "setuptools", "wheel"],
    tests_require=["pytest"],
)

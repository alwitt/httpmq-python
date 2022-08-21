from setuptools import find_packages, setup

setup(
    name="httpmq",
    version="0.1.0-rc.1",
    description="HTTP MQ Python client module",
    author="Rhine Cliff",
    author_email="rhinecliff@protonmail.com",
    packages=find_packages(exclude=["test", "scripts", "examples"]),
    scripts=[],
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "aiohttp",
        "aiostream",
        "asyncio",
        "python-dateutil",
    ],
)

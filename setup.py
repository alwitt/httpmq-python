from setuptools import find_packages, setup

setup(
    name="httpmq",
    version="0.1.0",
    description="HTTP MQ Python client module",
    author="Rhine Cliff",
    author_email="rhinecliff@protonmail.com",
    packages=find_packages(exclude=["test", "scripts"]),
    scripts=[],
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "python-dateutil",
        "urllib3; extra == 'secure,brotli'",
    ],
    setup_requires=["black", "flake8", "pylint", "setuptools", "wheel"],
    tests_require=["pytest"],
)

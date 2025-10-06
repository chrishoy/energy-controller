from setuptools import setup, find_packages

setup(
    name="energy-controller",
    version="0.1.0",
    description=(
        "A web service for monitoring and controlling energy usage "
        "with Octopus Energy"
    ),
    author="Chris Hoy",
    license="MIT",
    packages=find_packages(),
    install_requires=[
        "flask",
        "requests",
        "pytz",
        "python-dotenv",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.13",
    ],
    python_requires=">=3.8",
)

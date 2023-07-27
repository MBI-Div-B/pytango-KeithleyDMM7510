from setuptools import setup, find_packages

setup(
    name="tangods_keithleydmm7510",
    version="0.0.1",
    description="Tango Device Server for Keithley DMM7510 Digital Multimeter.",
    author="Daniel Schick",
    author_email="dschick@mbi-berlin.de",
    python_requires=">=3.6",
    entry_points={
        "console_scripts": ["KeithleyDMM7510 = tangods_keithleydmm7510:main"]
    },
    license="MIT",
    packages=["tangods_keithleydmm7510"],
    install_requires=[
        "pytango",
        "pyvisa",
    ],
    url="https://github.com/MBI-Div-b/pytango-KeithleyDMM7510",
    keywords=[
        "tango device",
        "tango",
        "pytango",
        "keitghley",
        "DMM7510",
    ],
)

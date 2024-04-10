from setuptools import setup, find_packages

setup(
    name='baseband_config',
    version='0.9',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'baseband_config = baseband_config.main:main',
        ],
    },
    description='A package for controlling the Baseband device using an USB-i2c interface.',
    author='PE1OBW',
    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='baseband i2c usb control',
    install_requires=['pyftdi', 'EasyMCP2221', 'PyMCP2221A'],
)

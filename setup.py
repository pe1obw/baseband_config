from setuptools import setup, find_packages

setup(
    name='baseband_config',
    version='1.0',
    packages=find_packages(),
    entry_points={
        'console_scripts': [
            'baseband_config = baseband_config.main:main',
        ],
    },
    description='A package for controlling the Baseband device using an USB-i2c interface.',
    author='PE1OBW',
    author_email='werner@pe1obw.com',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
    ],
    keywords='baseband i2c usb control',
    install_requires=['pyftdi'],
)

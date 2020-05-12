from setuptools import find_packages, setup
from clarity_ext_scripts import VERSION

setup(
    name='clarity-ext-scripts',
    version=VERSION,
    packages=find_packages(exclude=['tests']),
    package_data={'': ['*.j2', '*.txt', 'README']},
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: POSIX',
        'Operating System :: MacOS',
        'Operating System :: Unix',
        'Operating System :: Windows',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)

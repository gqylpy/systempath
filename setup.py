import setuptools
import pkg_resources
import gqylpy_filesystem as g

with open('README.md') as f:
    description = f.read()

with open('requirements.txt') as f:
    requires = [str(x) for x in pkg_resources.parse_requirements(f)]

setuptools.setup(
    name=g.__name__,
    version='1.0.alpha4',
    author='竹永康',
    author_email='gqylpy@outlook.com',
    license='Apache 2.0',
    url='http://gqylpy.com',
    project_urls={'Source': 'https://github.com/gqylpy/gqylpy-filesystem'},
    description=None,
    long_description=description,
    long_description_content_type='text/markdown',
    packages=[g.__name__],
    python_requires='>=3.6, <4',
    requires=requires,
    install_requires=requires,
    classifiers=[
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Topic :: Text Processing :: Indexing',
        'Topic :: Utilities',
        'Topic :: Internet',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ]
)

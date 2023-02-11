import setuptools
import pkg_resources
import systempath as g

from systempath import File

with File(g.__file__).open.r() as f:
    for line in f:
        if line.startswith('@version: ', 4):
            version = line.split()[-1]
            break
    author, email = f.readline().split(maxsplit=1)[-1].rstrip().split()
    source = f.readline().split()[-1]

with File('requirements.txt').open.r() as f:
    requires = [str(x) for x in pkg_resources.parse_requirements(f)]

setuptools.setup(
    name=g.__name__,
    version=version,
    author=author,
    author_email=email,
    license='Apache 2.0',
    url='http://gqylpy.com',
    project_urls={'Source': source},
    description='Operating system paths and files.',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    packages=[g.__name__],
    python_requires='>=3.8, <4',
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11'
    ]
)

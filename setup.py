import setuptools
import systempath as i

from systempath import Content

idoc: list = i.__doc__.split('\n')

for index, line in enumerate(idoc):
    if line.startswith('@version: ', 4):
        version = line.split()[-1]
        break
_, author, email = idoc[index + 1].split()
source = idoc[index + 2].split()[-1]

setuptools.setup(
    name=i.__name__,
    version=version,
    author=author,
    author_email=email,
    license='Apache 2.0',
    url='http://gqylpy.com',
    project_urls={'Source': source},
    description='Object-oriented operation of files and system paths.',
    long_description=open('README.md', encoding='utf8').read(),
    long_description_content_type='text/markdown',
    packages=[i.__name__],
    python_requires='>=3.8',
    install_requires=[x.decode() for x in Content('requirements.txt') if x],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: Chinese (Simplified)',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: System',
        'Topic :: System :: Filesystems',
        'Topic :: System :: Operating System',
        'Topic :: System :: Operating System Kernels :: Linux',
        'Topic :: System :: Systems Administration :: Authentication/Directory '
            ':: LDAP',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13'
    ]
)

import setuptools
import systempath as i
from systempath import File

idoc: list = i.__doc__.split('\n')

for index, line in enumerate(idoc):
    if line.startswith('@version: ', 4):
        version = line.split()[-1]
        break
_, author, email = idoc[index + 1].split()
source = idoc[index + 2].split()[-1]

requires_file, install_requires = \
    File('requirements.txt') or File('systempath.egg-info/requires.txt'), []

for require in requires_file:
    if not require:
        continue
    if require[0] == 91:
        break
    install_requires.append(require.decode())

setuptools.setup(
    name=i.__name__,
    version=version,
    author=author,
    author_email=email,
    license='Apache 2.0',
    url='http://gqylpy.com',
    project_urls={'Source': source},
    description='''
        The `systempath` is a library designed for Python developers, providing
        intuitive and powerful APIs that simplify file and directory management
        tasks, allowing developers to focus more on core business logic.
    '''.strip().replace('\n       ', ''),
    long_description=File('README.md').content.decode('utf-8'),
    long_description_content_type='text/markdown',
    packages=[i.__name__],
    python_requires='>=3.8',
    install_requires=install_requires,
    extras_require={'pyyaml': ['PyYAML>=6.0,<7.0']},
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

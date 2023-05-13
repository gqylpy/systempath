import re
import setuptools
import pkg_resources
import systempath as i

from systempath import File

version, author, email, source = re.search(
    ' {4}@version: ([1-9]\d*\.\d+(?:\.(?:alpha|beta)?\d+)?)\n'
    ' {4}@author: ([\u4e00-\u9fa5]{2,4}|[A-Z][a-z]+(?: [A-Z][a-z]+)?) (<.+?>)\n'
    ' {4}@source: (https?://.+)',
    i.__doc__,
).groups()

requires = [str(x) for x in pkg_resources.parse_requirements(
    open('requirements.txt', encoding='utf8')
)]

setuptools.setup(
    name=i.__name__,
    version=version,
    author=author,
    author_email=email,
    license='Apache 2.0',
    url='http://gqylpy.com',
    project_urls={'Source': source},
    description='Operating system paths and files.',
    long_description=open('README.md', encoding='utf8').read(),
    long_description_content_type='text/markdown',
    packages=[i.__name__],
    python_requires='>=3.8, <4',
    install_requires=requires,
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
        'Programming Language :: Python :: 3.11'
    ]
)

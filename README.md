[<img alt="LOGO" src="https://python.org/favicon.ico" height="21" width="21"/>](http://gqylpy.com)
[![Release](https://img.shields.io/github/release/gqylpy/systempath.svg?style=flat-square)](https://github.com/gqylpy/systempath/releases/latest)
[![Python Versions](https://img.shields.io/pypi/pyversions/systempath)](https://pypi.org/project/systempath)
[![License](https://img.shields.io/pypi/l/systempath)](https://github.com/gqylpy/systempath/blob/master/LICENSE)
[![Downloads](https://static.pepy.tech/badge/systempath)](https://pepy.tech/project/systempath)

# systempath
English | [中文](https://github.com/gqylpy/systempath/blob/master/README_CN.md)

**systempath** is a highly specialized library designed for Python developers for file and system path manipulation. By providing an intuitive and powerful object-oriented API, it significantly simplifies complex file and directory management tasks, allowing developers to focus more on implementing core business logic rather than the intricacies of low-level file system operations.

<kbd>pip3 install systempath</kbd>

```python
>>> from systempath import SystemPath, Directory, File

>>> root = SystemPath('/')

>>> home: Directory = root['home']['gqylpy']
>>> home
/home/gqylpy

>>> file: File = home['alpha.txt']
>>> file
/home/gqylpy/alpha.txt

>>> file.content
b'GQYLPY \xe6\x94\xb9\xe5\x8f\x98\xe4\xb8\x96\xe7\x95\x8c'
```

## Core Features

### 1. Object-Oriented Path Representation

- **Directory Class**: Specifically designed to represent directory paths, providing directory-specific operations such as traversal, creation, deletion, and management of subdirectories and files.
- **File Class**: Specifically designed to represent file paths, offering advanced functions beyond basic file operations, including content reading and writing, appending, and clearing.
- **SystemPath Class**: Serves as a universal interface for `Directory` and `File`, providing maximum flexibility to handle any type of path, whether it's a file or directory.

### 2. Automation and Flexibility

- **Automatic Absolute Path Conversion**: Supports automatically converting relative paths to absolute paths during path object initialization, reducing issues caused by incorrect paths.
- **Strict Mode**: Allows developers to enable strict mode, ensuring that paths do exist during initialization; otherwise, exceptions are thrown, enhancing code robustness and reliability.

### 3. Rich Operational Interfaces

- **Path Concatenation**: Supports path concatenation using `/`, `+` operators, and even brackets, making path construction more intuitive and flexible.
- **Comprehensive File and Directory Operations**: Provides a complete set of file and directory operation methods, including but not limited to reading, writing, copying, moving, deleting, and traversing, meeting various file processing needs.

## Usage Scenarios

- **Automation Script Development**: In scenarios such as automated testing, deployment scripts, log management, systempath offers powerful file and directory manipulation capabilities, simplifying script writing processes.
- **Web Application Development**: Handles user-uploaded files, generates temporary files, and more, making these operations simpler and more efficient with systempath.
- **Data Science and Analysis**: When reading, writing, and processing data files stored in the file system, systempath provides a convenient file management approach for data scientists.

## Conclusion

systempath is a comprehensive and easy-to-use library for file and system path manipulation. Through its object-oriented API design, it significantly simplifies the complexity of file and directory management in Python, allowing developers to focus more on implementing core business logic. Whether it's automation script development, web application building, or data science projects, systempath will be an indispensable and valuable assistant.

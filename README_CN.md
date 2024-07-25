[<img alt="LOGO" src="http://www.gqylpy.com/static/img/favicon.ico" height="21" width="21"/>](http://www.gqylpy.com)
[![Release](https://img.shields.io/github/release/gqylpy/systempath.svg?style=flat-square")](https://github.com/gqylpy/systempath/releases/latest)
[![Python Versions](https://img.shields.io/pypi/pyversions/systempath)](https://pypi.org/project/systempath)
[![License](https://img.shields.io/pypi/l/systempath)](https://github.com/gqylpy/systempath/blob/master/LICENSE)
[![Downloads](https://static.pepy.tech/badge/systempath)](https://pepy.tech/project/systempath)

# systempath - 专业级的文件与系统路径操作库
[English](README.md) | 中文

**systempath** 是一个专为Python开发者设计的，高度专业化的文件与系统路径操作库。通过提供一套直观且功能强大的面向对象API，它极大地简化了复杂文件与目录管理的任务，使开发者能够更专注于核心业务逻辑的实现，而非底层文件系统操作的细节。

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

## 核心特性

### 1. 面向对象的路径表示

- **Directory 类**：专门用于表示目录路径，提供目录遍历、创建、删除及子目录与文件管理等目录特定操作。
- **File 类**：专门用于表示文件路径，除了基本的文件操作外，还提供了内容读写、追加、清空等高级功能。
- **SystemPath 类**：作为 `Directory` 和 `File` 的通用接口，提供了最大的灵活性，能够处理任何类型的路径，无论是文件还是目录。

### 2. 自动化与灵活性

- **自动绝对路径转换**：支持在路径对象初始化时自动将相对路径转换为绝对路径，减少因路径错误导致的问题。
- **严格模式**：允许开发者启用严格模式，确保路径在初始化时确实存在，否则抛出异常，增强代码的健壮性和可靠性。

### 3. 丰富的操作接口

- **路径拼接**：支持使用 `/` 和 `+` 操作符甚至是中括号进行路径拼接，使得路径构建更加直观和灵活。
- **全面的文件与目录操作**：提供了一整套文件与目录操作方法，包括但不限于读取、写入、复制、移动、删除、遍历等，满足各种文件处理需求。

## 使用场景

- **自动化脚本开发**：在自动化测试、部署脚本、日志管理等场景中，systempath 提供强大的文件与目录操作能力，能够简化脚本编写过程。
- **Web应用开发**：处理用户上传的文件、生成临时文件等场景，systempath 使得这些操作更加简单高效。
- **数据科学与分析**：读取、写入和处理存储在文件系统中的数据文件时，systempath 为数据科学家提供了便捷的文件管理方式。

## 结论

systempath 是一个功能全面、易于使用的文件与系统路径操作库。通过其面向对象的API设计，它极大地简化了Python中文件与目录管理的复杂性，使得开发者能够更专注于核心业务逻辑的实现。无论是自动化脚本开发、Web应用构建，还是数据科学项目，systempath 都将是您不可或缺的得力助手。

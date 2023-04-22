[<img alt="LOGO" src="http://www.gqylpy.com/static/img/favicon.ico" height="21" width="21"/>](http://www.gqylpy.com)
[![Release](https://img.shields.io/github/release/gqylpy/systempath.svg?style=flat-square")](https://github.com/gqylpy/systempath/releases/latest)
[![Python Versions](https://img.shields.io/pypi/pyversions/systempath)](https://pypi.org/project/systempath)
[![License](https://img.shields.io/pypi/l/systempath)](https://github.com/gqylpy/systempath/blob/master/LICENSE)
[![Downloads](https://pepy.tech/badge/systempath/month)](https://pepy.tech/project/systempath)

# systempath

> (OOP) Operating system paths and files.  
> Let Python operating system paths and files become Simple, Simpler, Simplest, Humanization, Unification, Flawless.

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

>>> file.open.rb().read()
b'GQYLPY \xe6\x94\xb9\xe5\x8f\x98\xe4\xb8\x96\xe7\x95\x8c'
```

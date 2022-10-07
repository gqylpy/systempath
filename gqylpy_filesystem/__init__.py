"""
Copyright (c) 2022 GQYLPY <http://gqylpy.com>. All rights reserved.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    https://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""


class File:
    handle: 'TextIO'

    def __init__(
            self,
            file: 'Path',
            /, *,
            ftype: 'Literal["txt", "json", "yaml", "csv", "obj"]' = None,
            auto_ftype: bool = False
    ):
        self.file  = file
        self.ftype = ftype

    def open(self, **kw):
        if not self.handle:
            self.handle = open(self.file, **kw)
        return self.handle

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def __del__(self):
        if self.handle:
            self.handle.close()

    @property
    def basename(self) -> str:
        return os.path.basename(self.file)

    @property
    def basename_not_extension(self) -> str:
        return os.path.splitext(self.file)[0]

    @property
    def extension(self) -> 'Union[bytes, str]':
        return os.path.splitext(self.file)[1]

    @property
    def dirname(self) -> str:
        return os.path.dirname(self.file)

    def dirnamel(self, *, level: int = 1) -> str:
        directory: str = self.file
        for _ in range(level):
            directory = os.path.dirname(self.file)
        return directory

    @property
    def abspath(self) -> str:
        return self.file if os.path.isabs(self.file) \
            else os.path.abspath(self.file)

    def split(self) -> tuple:
        return os.path.split(self.file)

    def splitext(self) -> tuple:
        return os.path.splitext(self.file)

    def splitdrive(self) -> tuple:
        return os.path.splitdrive(self.file)

    def isabs(self) -> bool:
        return os.path.isabs(self.file)

    def exists(self) -> bool:
        return os.path.exists(self.file)

    def rename(self, dst: 'Path', /):
        if not os.path.abspath(dst):
            dst: Path = os.path.join(os.path.dirname(dst))
        os.rename(self.file, dst)
        self.file = os.path.abspath(dst)

    def move(self, dst: 'Path', /, *, copy_function=None) -> 'Path':
        dst: Path = shutil.move(self.file, dst, copy_function=copy_function)
        self.file = dst
        return dst

    def copy(self, dst: 'Path', /, *, follow_symlinks: bool = True) -> 'Path':
        return shutil.copyfile(self.file, dst, follow_symlinks=follow_symlinks)

    def copyobj(self, fdst: 'TextIO', /):
        with open(self.file) as fsrc:
            shutil.copyfileobj(fsrc, fdst)

    def truncate(self, length: int):
        os.truncate(self.file, length)

    def clear(self):
        os.truncate(self.file, 0)

    def mknod(
            self,
            mode:   int = None,
            device: int = None,
            *,
            dir_fd:    'Optional[int]' = None,
            ignore_err: bool           = False
    ):
        pass

    def remove(self):
        os.remove(self.file)

    @property
    def stat(self):
        return os.stat(self.file)

    @property
    def size(self):
        return os.path.getsize(self.file)

    @property
    def create_time(self):
        return os.path.getctime(self.file)

    @property
    def modify_time(self):
        return os.path.getmtime(self.file)

    @property
    def access_time(self):
        return os.path.getatime(self.file)

    def chmod(self, *a, **kw):
        raise NotImplementedError

    def chown(self, *a, **kw):
        raise NotImplementedError

    def chflags(self, *a, **kw):
        raise NotImplementedError


class _xe6_xad_x8c_xe7_x90_xaa_xe6_x80_xa1_xe7_x8e_xb2_xe8_x90_x8d_xe4_xba_x91:
    import sys

    __import__(f'{__name__}.g {__name__[7:]}')
    gpack = sys.modules[__name__]
    gcode = globals()[f'g {__name__[7:]}']

    for gname in globals():
        if gname[0] != '_' and hasattr(gcode, gname):
            setattr(gpack, gname, getattr(gcode, gname))


import os
import shutil
from os import PathLike

from typing import TextIO, Optional, Union, Literal


Path  = Union[str, bytes, PathLike[str], PathLike[bytes]]

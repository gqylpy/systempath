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
import os
import sys
import shutil

from os.path import (
    basename, dirname , abspath   , join    ,
    split   , splitext, splitdrive,
    isabs   , isfile  , exists    , lexists ,
    getsize , getctime, getmtime  , getatime
)

from typing import TextIO, Union, Literal, Tuple, Callable, Optional

import gqylpy_exception as ge

PathLink = BytesOrStr = Union[bytes, str]


class File:
    handle: TextIO = None

    def __init__(
            self,
            path: PathLink,
            /, *,
            ftype: Literal['txt', 'json', 'yaml', 'csv', 'obj']   = None,
            auto_ftype: bool  = False,
    ):
        if not isinstance(path, (str, bytes)):
            raise ge.ParamTypeError(
                'parameter "file" type can only be "bytes" or "str".')
        self.path  = path
        self.ftype = ftype

    def open(self, **kw) -> TextIO:
        if not self.handle:
            self.handle = open(self.path, **kw)
        return self.handle

    def __enter__(self) -> 'File':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __del__(self) -> None:
        self.handle and self.handle.close()

    @property
    def basename(self) -> BytesOrStr:
        return basename(self.path)

    @property
    def dirname(self) -> BytesOrStr:
        return dirname(self.path)

    def dirnamel(self, level: int) -> BytesOrStr:
        if self.path.__class__ is str:
            sep: str   = os.sep
        else:
            sep: bytes = os.sep.encode()
        return self.path.rsplit(sep, level)[0]

    @property
    def abspath(self) -> BytesOrStr:
        return abspath(self.path)

    def split(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return split(self.path)

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitext(self.path)

    @property
    def extension(self) -> BytesOrStr:
        return splitext(self.path)[1]

    def splitdrive(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitdrive(self.path)

    def isabs(self) -> bool:
        return isabs(self.path)

    def isfile(self) -> bool:
        return isfile(self.path)

    def exists(self) -> bool:
        return exists(self.path)

    def lexists(self) -> bool:
        return lexists(self.path)

    def rename(self, dst: PathLink, /) -> PathLink:
        dst: PathLink = self.abspath_if_not(dst)
        os.rename(self.path, dst)
        self.path = dst
        return dst

    def move(
            self,
            dst: PathLink,
            /, *,
            copy_function: Callable[[PathLink, PathLink], None] = shutil.copy2
    ) -> PathLink:
        dst: PathLink = self.abspath_if_not(dst)
        dst: PathLink = shutil.move(self.path, dst, copy_function)
        self.path = dst
        return dst

    def copy(
            self,
            dst: PathLink,
            /, *,
            follow_symlinks: bool = True
    ) -> PathLink:
        return shutil.copyfile(
            self.path, self.abspath_if_not(dst), follow_symlinks=follow_symlinks
        )

    def copyobj(self, fdst: TextIO, /) -> None:
        with open(self.path) as fsrc:
            shutil.copyfileobj(fsrc, fdst)

    def truncate(self, length: int):
        os.truncate(self.path, length)

    def clear(self):
        os.truncate(self.path, 0)

    if sys.platform == 'win32':
        def mknod(self, *_, ignore_err: bool = False, **__):
            if exists(self.path):
                if not ignore_err:
                    raise FileExistsError(f'file "{self.path}" already exists.')
            else:
                open(self.path, 'w').close()
    else:
        def mknod(
                self,
                mode:   int = None,
                device: int = None,
                *,
                dir_fd:     Optional[int] = None,
                ignore_err: bool          = False
        ):
            try:
                os.mknod(self.path, mode, device, dir_fd=dir_fd)
            except FileExistsError:
                if not ignore_err:
                    raise

    def remove(self):
        os.remove(self.path)

    @property
    def stat(self):
        return os.stat(self.path)

    @property
    def size(self):
        return getsize(self.path)

    @property
    def create_time(self):
        return getctime(self.path)

    @property
    def modify_time(self):
        return getmtime(self.path)

    @property
    def access_time(self):
        return getatime(self.path)

    def chmod(self, *a, **kw):
        raise NotImplementedError

    def chown(self, *a, **kw):
        raise NotImplementedError

    def chflags(self, *a, **kw):
        raise NotImplementedError

    def md5(self):
        raise NotImplementedError

    def abspath_if_not(self, path: PathLink) -> PathLink:
        if not isabs(path):
            path: PathLink = join(dirname(self.path), path)
        return path

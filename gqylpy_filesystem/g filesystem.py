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

from os import PathLike

from os.path import (
    basename, dirname ,  abspath   ,   join,
    split   , splitext,  splitdrive,
    isabs   , exists  ,
    getsize , getctime,  getmtime  ,   getatime
)

from typing import TextIO, Optional, Union

Path = Union[bytes, str, PathLike[bytes], PathLike[str]]


class File:
    handle: TextIO = None

    def __init__(
            self,
            file:       Path,
            /, *,
            ftype:      str   = None,
            auto_ftype: bool  = False
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
        return basename(self.file)

    @property
    def basename_not_extension(self) -> str:
        return splitext(self.file)[0]

    @property
    def extension(self) -> Union[bytes, str]:
        return splitext(self.file)[1]

    @property
    def dirname(self) -> str:
        return dirname(self.file)

    def dirnamel(self, *, level: int = 1) -> str:
        directory: str = self.file
        for _ in range(level):
            directory = dirname(self.file)
        return directory

    @property
    def abspath(self) -> str:
        return self.file if isabs(self.file) else abspath(self.file)

    def split(self) -> tuple:
        return split(self.file)

    def splitext(self) -> tuple:
        return splitext(self.file)

    def splitdrive(self) -> tuple:
        return splitdrive(self.file)

    def isabs(self) -> bool:
        return isabs(self.file)

    def exists(self) -> bool:
        return exists(self.file)

    def rename(self, dst: Path, /):
        if not abspath(dst):
            dst: Path = join(dirname(dst))
        os.rename(self.file, dst)
        self.file = abspath(dst)

    def move(self, dst: Path, /, *, copy_function=shutil.copy2) -> Path:
        """
        移动文件时，若目标路径是相对路径，将以当前工作目录作为上级路径（`os.getcwd()`的返回值）
        """
        dst: Path = shutil.move(self.file, dst, copy_function=copy_function)
        self.file = dst
        return dst

    def copy(self, dst: Path, /, *, follow_symlinks: bool = True) -> Path:
        """
        目标路径必须是一个文件，目标存在则覆盖。如目标是源文件则引发shutil.SameFileError。
        返回文件的目的地。
        复制文件时，若目标路径是相对路径，将以当前工作目录作为上级路径（`os.getcwd()`的返回值）
        """
        return shutil.copyfile(self.file, dst, follow_symlinks=follow_symlinks)

    def copyobj(self, fdst: TextIO, /):
        """
        将文件内容复制到目的地，若目的地不可写，将引发io.UnsupportedOperation
        """
        with open(self.file) as fsrc:
            shutil.copyfileobj(fsrc, fdst)

    def truncate(self, length: int):
        os.truncate(self.file, length)

    def clear(self):
        os.truncate(self.file, 0)

    if sys.platform == 'win32':
        def mknod(self, *_, ignore_err: bool = False, **__):
            if exists(self.file):
                if not ignore_err:
                    raise FileExistsError(f'file "{self.file}" already exists.')
            else:
                open(self.file, 'w').close()
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
                os.mknod(self.file, mode, device, dir_fd=dir_fd)
            except FileExistsError:
                if not ignore_err:
                    raise

    def remove(self):
        os.remove(self.file)

    @property
    def stat(self):
        return os.stat(self.file)

    @property
    def size(self):
        return getsize(self.file)

    @property
    def create_time(self):
        return getctime(self.file)

    @property
    def modify_time(self):
        return getmtime(self.file)

    @property
    def access_time(self):
        return getatime(self.file)

    def chmod(self, *a, **kw):
        raise NotImplementedError

    def chown(self, *a, **kw):
        raise NotImplementedError

    def chflags(self, *a, **kw):
        raise NotImplementedError

    def md5(self):
        pass

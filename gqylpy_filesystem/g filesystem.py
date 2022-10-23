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
import sys
import shutil
import functools

from os import (
    sep, stat, stat_result, system, popen,
    rename, remove, chmod, truncate, access
)

try:
    from os import mknod, chown, chflags
except ImportError:
    pass

from os.path import (
    basename, dirname , abspath   , join    ,
    split   , splitext, splitdrive,
    isabs   , isfile  , exists    , lexists ,
    getsize , getctime, getmtime  , getatime
)

from typing import TextIO, Union, Literal, Tuple, Callable, Optional, Any

import gqylpy_exception as ge

PathLink = BytesOrStr = Union[bytes, str]


class File:

    def __init__(
            self,
            path:  PathLink,
            /, *,
            ftype: Literal['txt', 'json', 'yaml', 'csv', 'obj'] = None
    ):
        if not isinstance(path, (str, bytes)):
            raise ge.ParamTypeError(
                'parameter "file" type can only be "bytes" or "str".')
        self.path  = path
        self.ftype = ftype

    @staticmethod
    def changeable_else_raise(
            func: Callable[['File', str, Optional[Any]], None]
    ) -> Callable:
        unchangeable = 'path',

        @functools.wraps(func)
        def inner(self: 'File', name: str, *a) -> None:
            if (
                    name in unchangeable and
                    sys._getframe(1).f_globals['__name__'] != __name__
            ):
                raise ge[f'{func.__name__[2:-2].capitalize()}Error'](
                    f'attribute "{name}" is unchangeable.')
            func(self, name, *a)

        return inner

    @changeable_else_raise
    def __setattr__(self, name: str, value: Any):
        super().__setattr__(name, value)

    @changeable_else_raise
    def __delattr__(self, name: str):
        super().__delattr__(name)

    def __del__(self):
        pass

    def open(self, **kw) -> TextIO:
        raise NotImplementedError

    @property
    def basename(self) -> BytesOrStr:
        return basename(self.path)

    @property
    def dirname(self) -> BytesOrStr:
        return dirname(self.path)

    def dirnamel(self, level: int) -> BytesOrStr:
        return self.path.rsplit(
            sep if self.path.__class__ is str else sep.encode(),
            maxsplit=level
        )[0]

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
        rename(self.path, dst)
        self.path = dst
        return dst

    def move(
            self,
            dst:           PathLink,
            /, *,
            copy_function: Callable[[PathLink, PathLink], None] = shutil.copy2
    ) -> PathLink:
        dst: PathLink = self.abspath_if_not(dst)
        dst: PathLink = shutil.move(self.path, dst, copy_function)
        self.path = dst
        return dst

    def copy(
            self,
            dst:             PathLink,
            /, *,
            follow_symlinks: bool     = True
    ) -> PathLink:
        return shutil.copyfile(
            src=self.path,
            dst=self.abspath_if_not(dst),
            follow_symlinks=follow_symlinks
        )

    def copyobj(self, fdst: TextIO, /) -> None:
        with open(self.path) as fsrc:
            shutil.copyfileobj(fsrc, fdst)

    def truncate(self, length: int) -> None:
        truncate(self.path, length)

    def clear(self) -> None:
        truncate(self.path, 0)

    if sys.platform == 'win32':
        def mknod(
                self,
                mode:          int  = 0o600,
                *_,
                ignore_exists: bool = False,
                **__
        ) -> None:
            if not exists(self.path):
                open(self.path, 'w').close()
                chmod(self.path, mode)
            elif not ignore_exists:
                raise FileExistsError(f'file "{self.path}" already exists.')
    else:
        def mknod(
                self,
                mode:          int           = None,
                *,
                device:        int           = 0,
                dir_fd:        Optional[int] = None,
                ignore_exists: bool          = False
        ) -> None:
            try:
                mknod(self.path, mode, device, dir_fd=dir_fd)
            except FileExistsError:
                if not ignore_exists:
                    raise

    def remove(self) -> None:
        remove(self.path)

    @property
    def stat(self) -> stat_result:
        return stat(self.path)

    @property
    def size(self) -> int:
        return getsize(self.path)

    @property
    def create_time(self) -> float:
        return getctime(self.path)

    @property
    def modify_time(self) -> float:
        return getmtime(self.path)

    @property
    def access_time(self) -> float:
        return getatime(self.path)

    def chmod(
            self,
            mode:            int,
            *,
            dir_fd:          Optional[int] = None,
            follow_symlinks: bool          = True
    ) -> None:
        chmod(
            path           =self.path,
            mode           =mode,
            dir_fd         =dir_fd,
            follow_symlinks=follow_symlinks
        )

    def access(
            self,
            mode:            int,
            *,
            dir_fd:          Optional[int] = None,
            effective_ids:   bool          = False,
            follow_symlinks: bool          = True
    ) -> bool:
        return access(
            path           =self.path,
            mode           =mode,
            dir_fd         =dir_fd,
            effective_ids  =effective_ids,
            follow_symlinks=follow_symlinks
        )

    if sys.platform != 'win32':
        def chown(
                self,
                uid:             int,
                gid:             int,
                *,
                dir_fd:          Optional[int] = int,
                follow_symlinks: bool          = True
        ) -> None:
            return chown(
                path           =self.path,
                uid            =uid,
                gid            =gid,
                dir_fd         =dir_fd,
                follow_symlinks=follow_symlinks
            )

        def chflags(self):
            raise NotImplementedError

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            if operator not in ('+', '-', '='):
                raise ge.ChattrOperatorError(
                    f'Unsupported operation "{operator}", only "+", "-" or "=".'
                )
            c: str = f'chattr {operator}{attrs} {self.path}'
            if system(f'sudo {c} &>/dev/null'):
                raise ge.ChattrExecuteError(c)

        def lsattr(self) -> str:
            c: str = f'lsattr {self.path}'
            attrs: str = popen(
                "sudo %s 2>/dev/null | awk '{print $1}'" % c
            ).read()[:-1]
            if len(attrs) != 16:
                raise ge.LsattrExecuteError(c)
            return attrs

        def exattr(self, attr: str, /) -> bool:
            return attr in self.lsattr()

    def md5(self):
        raise NotImplementedError

    def abspath_if_not(self, path: PathLink) -> PathLink:
        if not isabs(path):
            path: PathLink = join(dirname(self.path), path)
        return path

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
import hashlib
import warnings
import functools

from os import (
    stat, lstat, stat_result,
    rename, renames, replace, remove, chmod, truncate, access, link, symlink
)

if sys.platform != 'win32':
    from os import mknod, chown, system, popen

    if sys.platform == 'linux':
        from os import getxattr, listxattr, removexattr, setxattr

    try:
        from os import lchmod, chflags, lchflags
    except ImportError:
        def lchmod(_): raise NotImplementedError
        chflags = lchflags = lchmod

from os.path import (
    basename, dirname , abspath   , relpath,  join  ,
    split   , splitext, splitdrive,
    isabs   , isfile  , exists    , lexists , islink,
    getsize , getctime, getmtime  , getatime
)

from shutil import move, copyfile, copystat, copymode, copy2

from typing import \
    TextIO, BinaryIO, Literal, Optional, Union, Tuple, List, Callable

import gqylpy_exception as ge

PathLink = BytesOrStr = Union[bytes, str]


def dst2abs(
        func: Callable[['File', PathLink], None]
) -> Callable[['File', PathLink], PathLink]:
    # If the destination path is relative and is a single name, the parent path
    # of the source is used as the parent path of the destination instead of
    # using the current working directory, different from the traditional way.
    @functools.wraps(func)
    def core(file: 'File', dst: PathLink) -> PathLink:
        try:
            single_name: bool = basename(dst) == dst
        except TypeError:
            raise ge.DestinationPathTypeError(
                'destination path type can only be "bytes" or "str".'
            )
        if single_name:
            try:
                dst: PathLink = join(file.dirname, dst)
            except TypeError:
                dst: PathLink = join(dirname(
                    file.path.decode() if dst.__class__ is str
                    else file.path.encode()
                ), dst)
        func(file, dst)
        file._File__path = dst
        return dst
    return core


class File:

    def __init__(
            self,
            path:  PathLink,
            /, *,
            ftype: Literal['txt', 'json', 'yaml', 'csv', 'obj'] = None,
            autoabs: bool = False,
            dir_fd: Optional[int] = None,
            follow_symlinks: bool = True
    ):
        if path.__class__ not in (str, bytes):
            raise ge.FilePathTypeError(
                'file path type can only be "bytes" or "str".'
            )
        self.__path          = path
        self.ftype           = ftype
        self.autoabs         = autoabs
        self.dir_fd          = dir_fd
        self.follow_symlinks = follow_symlinks

    def open(self, **kw) -> Union[BinaryIO, TextIO]:
        raise NotImplementedError

    @property
    def path(self) -> PathLink:
        return self.__path

    def neatpath(self) -> None:
        if not self.autoabs:
            self.__path = abspath(self.path)

    @property
    def basename(self) -> BytesOrStr:
        return basename(self.path)

    @property
    def dirname(self) -> BytesOrStr:
        return dirname(self.path)

    def dirnamel(self, level: int) -> BytesOrStr:
        dir: BytesOrStr = self.path
        for _ in range(level):
            dir: BytesOrStr = dirname(dir)
        return dir

    @property
    def abspath(self) -> BytesOrStr:
        return abspath(self.path)

    realpath = abspath

    def relpath(self, start: Optional[PathLink] = None):
        return relpath(self.path, start=start)

    def split(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return split(self.path)

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitext(self.path)

    @property
    def extension(self) -> BytesOrStr:
        return splitext(self.path)[1]

    def splitdrive(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitdrive(self.path)

    @property
    def isabs(self) -> bool:
        return isabs(self.path)

    @property
    def isfile(self) -> bool:
        return isfile(self.path)

    @property
    def exists(self) -> bool:
        return exists(self.path)

    @property
    def lexists(self) -> bool:
        return lexists(self.path)

    @property
    def islink(self) -> bool:
        return islink(self.path)

    @property
    def readable(self) -> bool:
        return access(
            path           =self.path,
            mode           =4,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def writeable(self) -> bool:
        return access(
            path           =self.path,
            mode           =2,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def executable(self) -> bool:
        return access(
            path           =self.path,
            mode           =1,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @dst2abs
    def rename(self, dst: PathLink, /) -> None:
        rename(self.path, dst, src_dir_fd=self.dir_fd, dst_dir_fd=self.dir_fd)

    @dst2abs
    def renames(self, dst: PathLink, /) -> None:
        renames(self.path, dst)

    @dst2abs
    def replace(self, dst: PathLink, /) -> None:
        replace(self.path, dst, src_dir_fd=self.dir_fd, dst_dir_fd=self.dir_fd)

    def move(
            self,
            dst:           PathLink,
            /, *,
            copy_function: Callable[[PathLink, PathLink], None] = copy2
    ) -> PathLink:
        return move(self.path, dst, copy_function=copy_function)

    def copy(self, dst: PathLink, /) -> PathLink:
        return copyfile(
            src            =self.path,
            dst            =dst,
            follow_symlinks=self.follow_symlinks
        )

    def copystat(self, dst: PathLink, /) -> None:
        copystat(self.path, dst, follow_symlinks=self.follow_symlinks)

    def copymode(self, dst: PathLink, /) -> None:
        copymode(self.path, dst, follow_symlinks=self.follow_symlinks)

    def copycontent(
            self,
            fdst:   BinaryIO,
            /, *,
            buffer: int = 1024 * 1024 if sys.platform == 'win32' else 64 * 1024
    ) -> None:
        fsrc: BinaryIO = open(self.path, 'rb')
        try:
            reader, writer = fsrc.read, fdst.write
            while True:
                content = reader(buffer)
                if not content:
                    break
                writer(content)
        finally:
            fsrc.close()

    def link(self, dst: PathLink, /) -> None:
        link(
            src            =self.path,
            dst            =dst,
            src_dir_fd     =self.dir_fd,
            dst_dir_fd     =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def symlink(self, dst: PathLink, /) -> None:
        symlink(self.path, dst, dir_fd=self.dir_fd)

    def truncate(self, length: int) -> None:
        truncate(self.path, length)

    def clear(self) -> None:
        truncate(self.path, 0)

    def remove(self) -> None:
        remove(self.path)

    @property
    def stat(self) -> stat_result:
        return stat(
            path           =self.path,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def lstat(self) -> stat_result:
        return lstat(self.path, dir_fd=self.dir_fd)

    def getsize(self) -> int:
        return getsize(self.path)

    def getctime(self) -> float:
        return getctime(self.path)

    def getmtime(self) -> float:
        return getmtime(self.path)

    def getatime(self) -> float:
        return getatime(self.path)

    def chmod(self, mode: int, /) -> None:
        chmod(
            path           =self.path,
            mode           =mode,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def access(self, mode: int, /, *, effective_ids: bool = False) -> bool:
        return access(
            path           =self.path,
            mode           =mode,
            dir_fd         =self.dir_fd,
            effective_ids  =effective_ids,
            follow_symlinks=self.follow_symlinks
        )

    if sys.platform != 'win32':
        def mknod(
                self,
                mode:          int  = None,
                *,
                device:        int  = 0,
                ignore_exists: bool = False
        ) -> None:
            try:
                mknod(self.path, mode, device, dir_fd=self.dir_fd)
            except FileExistsError:
                if not ignore_exists:
                    raise

        def lchmod(self, mode: int, /) -> None:
            lchmod(self.path, mode)

        def chown(self, uid: int, gid: int) -> None:
            return chown(
                path           =self.path,
                uid            =uid,
                gid            =gid,
                dir_fd         =self.dir_fd,
                follow_symlinks=self.follow_symlinks
            )

        def lchown(self, uid: int, gid: int) -> None:
            chown(self.path, uid, gid)

        def chflags(self, flags: int) -> None:
            chflags(self.path, flags, self.follow_symlinks)

        def lchflags(self, flags: int) -> None:
            lchflags(self.path, flags)

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            warnings.warn(UseWarning(
                'implementation of method `chattr` is to directly call the '
                'system command `chattr`, so this is very unreliable.'
            ))
            if operator not in ('+', '-', '='):
                raise ge.ChattrOperatorError(
                    f'unsupported operation "{operator}", only "+", "-" or "=".'
                )
            c: str = f'chattr {operator}{attrs} {self.path}'
            if system(f'sudo {c} &>/dev/null'):
                raise ge.ChattrExecuteError(c)

        def lsattr(self) -> str:
            warnings.warn(UseWarning(
                'implementation of method `lsattr` is to directly call the '
                'system command `lsattr`, so this is very unreliable.'
            ))
            c: str = f'lsattr {self.path}'
            attrs: str = popen(
                "sudo %s 2>/dev/null | awk '{print $1}'" % c
            ).read()[:-1]
            if len(attrs) != 16:
                raise ge.LsattrExecuteError(c)
            return attrs

        def exattr(self, attr: str, /) -> bool:
            return attr in self.lsattr()

        if sys.platform == 'linux':
            def getxattr(self, attribute: BytesOrStr, /) -> bytes:
                return getxattr(
                    path           =self.path,
                    attribute      =attribute,
                    follow_symlinks=self.follow_symlinks
                )

            def listxattr(self) -> List[str]:
                return listxattr(
                    path           =self.path,
                    follow_symlinks=self.follow_symlinks
                )

            def removexattr(self, attribute: BytesOrStr, /) -> None:
                removexattr(
                    path           =self.path,
                    attribute      =attribute,
                    follow_symlinks=self.follow_symlinks
                )

            def setxattr(
                    self,
                    attribute: BytesOrStr,
                    value:     bytes,
                    *,
                    flags:     int        = 0
            ) -> None:
                setxattr(
                    path     =self.path,
                    attribute=attribute,
                    value    =value,
                    flags    =flags
                )
    else:
        def mknod(
                self,
                mode:          int  = 0o600,
                *a,
                ignore_exists: bool = False,
                **kw
        ) -> None:
            if not exists(self.path):
                open(self.path, 'x').close()
                chmod(self.path, mode)
            elif not ignore_exists:
                raise FileExistsError(f'file "{self.path}" already exists.')

    @property
    def md5(self, salting: bytes = b'', /) -> str:
        md5 = hashlib.md5(salting)
        with open(self.path, 'rb') as f:
            while True:
                content = f.read(self.copycontent.__kwdefaults__['buffer'])
                if not content:
                    break
                md5.update(content)
        return md5.hexdigest()


class UseWarning(Warning):
    ...

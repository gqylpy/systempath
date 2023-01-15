"""
Copyright (c) 2022, 2023 GQYLPY <http://gqylpy.com>. All rights reserved.

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
import builtins
import warnings
import functools

from os import (
    stat,   lstat,   stat_result,
    rename, renames, replace,     remove,
    chmod,  access,  truncate,
    link,   symlink, unlink,      readlink
)

if sys.platform != 'win32':
    from os import mknod, chown, system, popen

    if sys.platform == 'linux':
        from os import getxattr, setxattr, listxattr, removexattr

    try:
        from os import lchmod, chflags, lchflags
    except ImportError:
        def lchmod(_): raise NotImplementedError
        chflags = lchflags = lchmod

    READ_BUFFER_SIZE = 1024 * 64
else:
    READ_BUFFER_SIZE = 1024 * 1024

from os.path import (
    basename, dirname,  abspath,    relpath,
    join,     split,    splitext,   splitdrive,
    isabs,    isfile,   exists,     lexists,    islink,
    getctime, getmtime, getatime,   getsize
)

from shutil import move, copyfile, copystat, copymode, copy2

from _io import (
    FileIO, BufferedReader, BufferedWriter, BufferedRandom, TextIOWrapper,
    _BufferedIOBase     as BufferedIOBase,
    DEFAULT_BUFFER_SIZE as OI_BUFFER_SIZE
)

from _hashlib import openssl_md5, HASH

from typing import (
    Literal, Optional, Type, TypeVar, Union, Tuple, List, Callable, Iterable,
    Any
)

import gqylpy_exception as ge

BytesOrStr = TypeVar('BytesOrStr', bytes, str)
PathLink   = BytesOrStr
Closure    = TypeVar('Closure', bound=Callable)

OpenMode = Literal[
    'rb', 'rb_plus', 'rt', 'rt_plus', 'r', 'r_plus',
    'wb', 'wb_plus', 'wt', 'wt_plus', 'w', 'w_plus',
    'ab', 'ab_plus', 'at', 'at_plus', 'a', 'a_plus',
    'xb', 'xb_plus', 'xt', 'xt_plus', 'x', 'x_plus'
]

EncodingErrorHandlingMode = Literal[
    'strict',
    'ignore',
    'replace',
    'surrogateescape',
    'xmlcharrefreplace',
    'backslashreplace',
    'namereplace'
]


class MasqueradeClass(type):
    # Masquerade one class as another.
    # Warning, masquerade the class can cause unexpected problems, use caution.
    __module__ = 'builtins'

    def __new__(mcs, __name__: str, __bases__: tuple, __dict__: dict):
        try:
            __masquerade_class__ = __dict__['__masquerade_class__']
        except KeyError:
            raise AttributeError(
                f'instance of "{mcs.__name__}" must '
                'define "__masquerade_class__" attribute, '
                'use to specify the class to disguise.'
            )

        if not isinstance(__masquerade_class__, type):
            raise TypeError('"__masquerade_class__" is not a class.')

        cls = type.__new__(
            mcs, __masquerade_class__.__name__, __bases__, __dict__
        )

        mcs.__name__     = type.__name__
        cls.__module__   = __masquerade_class__.__module__
        cls.__qualname__ = __masquerade_class__.__qualname__

        if getattr(builtins, __masquerade_class__.__name__, None) is \
                __masquerade_class__:
            setattr(builtins, __name__, cls)

        return cls

    def __hash__(cls):
        return hash(cls.__masquerade_class__)

    def __eq__(cls, o):
        return True if o is cls.__masquerade_class__ else super().__eq__(o)


class ReadOnlyMode(type, metaclass=MasqueradeClass):
    # Disallow modifying the attributes of the classes externally.
    __masquerade_class__ = type

    def __setattr__(cls, name: str, value: Any) -> None:
        if sys._getframe().f_back.f_globals['__package__'] != __package__:
            raise ge.SetAttributeError(
                f'cannot set "{name}" attribute '
                f'of immutable type "{cls.__name__}".'
            )
        super().__setattr__(name, value)


class ReadOnly(metaclass=ReadOnlyMode):
    # Disallow modifying the attributes of the instances externally.
    __dict__ = {}

    def __setattr__(self, name: str, value: Any) -> None:
        if sys._getframe().f_back.f_globals['__name__'] != __name__:
            raise ge.SetAttributeError(
                f'cannot set "{name}" attribute in instance '
                f'of immutable type "{self.__class__.__name__}".'
            )
        super().__setattr__(name, value)


def dst2abs(func: Callable) -> Closure:
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
        file.path = dst
        return dst
    return core


def dst2path(func: Callable) -> Closure:
    # If the destination path is instance of `File` then convert to path link.
    @functools.wraps(func)
    def core(
            file: 'File', dst: Union['File', PathLink], **kw
    ) -> Union['File', PathLink]:
        func(file, dst.path if isinstance(dst, File) else dst, **kw)
        return dst
    return core


class File(ReadOnly):

    def __init__(
            self,
            path:            PathLink,
            /, *,
            follow_symlinks: bool          = True,
            dir_fd:          Optional[int] = None
    ):
        if path.__class__ not in (str, bytes):
            raise ge.FileError(
                'file path type can only be "bytes" or "str", '
                f'not "{path.__class__.__name__}".'
            )
        self.path            = path
        self.dir_fd          = dir_fd
        self.follow_symlinks = follow_symlinks

    def __str__(self) -> str:
        path = self.path
        if path.__class__ is str:
            path = '"' + path + '"'
        return f'<{__package__}.{File.__name__} path={path}>'

    __repr__ = __str__

    @property
    def open(self) -> 'Open':
        return Open(self.path)

    @property
    def name(self) -> PathLink:
        return self.path

    @property
    def basename(self) -> BytesOrStr:
        return basename(self.path)

    @property
    def dirname(self) -> PathLink:
        return dirname(self.path)

    def dirnamel(self, level: int) -> PathLink:
        dir: PathLink = self.path
        for _ in range(level):
            dir: PathLink = dirname(dir)
        return dir

    @property
    def abspath(self) -> PathLink:
        return abspath(self.path)

    realpath = abspath

    def relpath(self, start: Optional[PathLink] = None):
        return relpath(self.path, start=start)

    def split(self) -> Tuple[PathLink, BytesOrStr]:
        return split(self.path)

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitext(self.path)

    @property
    def extension(self) -> BytesOrStr:
        return splitext(self.path)[1]

    def splitdrive(self) -> Tuple[BytesOrStr, PathLink]:
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
            self.path, 4,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def writeable(self) -> bool:
        return access(
            self.path, 2,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def executable(self) -> bool:
        return access(
            self.path, 1,
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

    @dst2path
    def move(
            self,
            dst:           PathLink,
            /, *,
            copy_function: Callable[[PathLink, PathLink], None] = copy2
    ) -> None:
        move(self.path, dst, copy_function=copy_function)

    @dst2path
    def copy(self, dst: PathLink, /) -> None:
        copyfile(self.path, dst, follow_symlinks=self.follow_symlinks)

    @dst2path
    def copystat(self, dst: PathLink, /) -> None:
        copystat(self.path, dst, follow_symlinks=self.follow_symlinks)

    @dst2path
    def copymode(self, dst: PathLink, /) -> None:
        copymode(self.path, dst, follow_symlinks=self.follow_symlinks)

    def copycontent(
            self,
            other:   Union['File', FileIO],
            /, *,
            bufsize: int                   = READ_BUFFER_SIZE
    ) -> Union['File', FileIO]:
        write = (
            FileIO(other.path, 'wb') if isinstance(other, File) else other
        ).write
        read = FileIO(self.path).read
        while True:
            content: bytes = read(bufsize)
            if not content:
                break
            write(content)
        return other

    @dst2path
    def link(self, dst: PathLink, /) -> None:
        link(
            self.path, dst,
            src_dir_fd     =self.dir_fd,
            dst_dir_fd     =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @dst2path
    def symlink(self, dst: PathLink, /) -> None:
        symlink(self.path, dst, dir_fd=self.dir_fd)

    def readlink(self) -> PathLink:
        return readlink(self.path, dir_fd=self.dir_fd)

    def truncate(self, length: int) -> None:
        truncate(self.path, length)

    def clear(self) -> None:
        truncate(self.path, 0)

    def remove(self) -> None:
        remove(self.path)

    def unlink(self) -> None:
        unlink(self.path, dir_fd=self.dir_fd)

    @property
    def stat(self) -> stat_result:
        return stat(
            self.path,
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
            self.path, mode,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def access(self, mode: int, /, *, effective_ids: bool = False) -> bool:
        return access(
            self.path, mode,
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
                self.path, uid, gid,
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
            warnings.warn(UserWarning(
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
            warnings.warn(UserWarning(
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
                    self.path, attribute,
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
                    self.path, attribute, value, flags,
                    follow_symlinks=self.follow_symlinks
                )

            def listxattr(self) -> List[str]:
                return listxattr(
                    self.path, follow_symlinks=self.follow_symlinks
                )

            def removexattr(self, attribute: BytesOrStr, /) -> None:
                removexattr(
                    self.path, attribute, follow_symlinks=self.follow_symlinks
                )

    else:
        def mknod(
                self,
                mode:          int  = 0o600,
                *,
                ignore_exists: bool = False,
                **__
        ) -> None:
            try:
                FileIO(self.path, 'xb')
            except FileExistsError:
                if not ignore_exists:
                    raise
            else:
                chmod(self.path, mode)

    def md5(self, salting: bytes = b'') -> str:
        md5: HASH = openssl_md5(salting)
        read = FileIO(self.path).read

        while True:
            content = read(READ_BUFFER_SIZE)
            if not content:
                break
            md5.update(content)

        return md5.hexdigest()


class Open(ReadOnly):
    __modes__ = {
        'r': BufferedReader,
        'w': BufferedWriter,
        'x': BufferedWriter,
        'a': BufferedWriter
    }
    for mode in tuple(__modes__):
        mode_b, mode_t = mode + 'b', mode + 't'
        __modes__[mode_b] = __modes__[mode_t] = __modes__[mode]
        __modes__[mode   + '_plus'] = BufferedRandom
        __modes__[mode_b + '_plus'] = BufferedRandom
        __modes__[mode_t + '_plus'] = BufferedRandom
    del mode, mode_b, mode_t

    def __init__(self, file: Union[File, PathLink], /):
        if not isinstance(file, (bytes, str, File)):
            raise ge.OpenError(
                f'file to be opened can only be an instance of '
                f'"{__package__}.{File.__name__}" or a path link, '
                f'not "{file.__class__.__name__}".'
            )
        self.file = file

    def __getattr__(self, mode: OpenMode) -> Closure:
        try:
            buffer: Type[BufferedIOBase] = Open.__modes__[mode]
        except KeyError:
            raise AttributeError(
                f"'{Open.__name__}' object has no attribute '{mode}'"
            )
        return self.__pass__(buffer, mode)

    def __dir__(self) -> Iterable[str]:
        methods = object.__dir__(self)
        methods.remove('__modes__')
        methods.remove('__pass__')
        methods.remove('__path__')
        methods += self.__modes__
        return methods

    def __str__(self) -> str:
        path = self.__path__
        if path.__class__ is str:
            path = '"' + path + '"'
        return f'<{__package__}.{Open.__name__} file={path}>'

    __repr__ = __str__

    @property
    def __path__(self) -> PathLink:
        return self.file.path if isinstance(self.file, File) else self.file

    def __pass__(self, buffer: Type[BufferedIOBase], mode: OpenMode) -> Closure:
        def init_buffer_instance(
                *,
                bufsize:        int                            = OI_BUFFER_SIZE,
                encoding:       Optional[str]                       = None,
                errors:         Optional[EncodingErrorHandlingMode] = None,
                newline:        Optional[str]                       = None,
                line_buffering: bool                                = False,
                write_through:  bool                                = False,
                opener:         Optional[Callable[[PathLink, int], int]] = None
        ) -> Union[BufferedIOBase, TextIOWrapper]:
            buf: BufferedIOBase = buffer(
                raw=FileIO(
                    file  =self.__path__,
                    mode  =mode.replace('_plus', '+'),
                    opener=opener
                ),
                buffer_size=bufsize
            )
            return buf if 'b' in mode else TextIOWrapper(
                buffer        =buf,
                encoding      =encoding,
                errors        =errors,
                newline       =newline,
                line_buffering=line_buffering,
                write_through =write_through
            )

        init_buffer_instance.__name__     = mode
        init_buffer_instance.__qualname__ = f'{Open.__name__}.{mode}'

        return init_buffer_instance

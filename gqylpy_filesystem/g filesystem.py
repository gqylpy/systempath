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
    stat,    lstat,   stat_result,
    rename,  renames, replace,     remove,
    chmod,   access,  truncate,    utime,
    link,    symlink, unlink,      readlink,
    listdir, scandir, walk,        chdir,
    mkdir,   rmdir,   makedirs,    removedirs,
    sep
)

if sys.platform != 'win32':
    from os import mknod, chown, system, popen

    if sys.platform == 'linux':
        from os import getxattr, setxattr, listxattr, removexattr

    try:
        from os import lchmod, lchown, chflags, lchflags
    except ImportError:
        def lchmod(*a, **kw): raise NotImplementedError
        lchown = chflags = lchflags = lchmod

    READ_BUFFER_SIZE = 1024 * 64
else:
    READ_BUFFER_SIZE = 1024 * 1024
    sys.setrecursionlimit(10000)

from os.path import (
    basename, dirname,  abspath,  relpath,
    join,     split,    splitext, splitdrive,
    isabs,    exists,   lexists,  isdir,      isfile, islink, ismount,
    getctime, getmtime, getatime, getsize
)

from shutil import move, copyfile, copytree, copystat, copymode, copy2, rmtree

from _io import (
    FileIO, BufferedReader, BufferedWriter, BufferedRandom, TextIOWrapper,
    _BufferedIOBase     as BufferedIOBase,
    DEFAULT_BUFFER_SIZE as IO_BUFFER_SIZE
)

from _hashlib import openssl_md5, HASH

from typing import (
    TypeVar, Literal, Optional, Type, Union, Tuple, List, Callable, Generator,
    Iterator, Iterable, Any
)

import gqylpy_exception as ge

PathLink = BytesOrStr = Union[bytes, str]
Closure = TypeVar('Closure', bound=Callable)

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

sepb: bytes = sep.encode()


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
        if name not in ('content', 'contents') and \
                sys._getframe().f_back.f_globals['__name__'] != __name__:
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
    def core(path: 'Path', dst: PathLink) -> PathLink:
        try:
            single_name: bool = basename(dst) == dst
        except TypeError:
            raise ge.DestinationPathTypeError(
                'destination path type can only be "bytes" or "str".'
            )
        if single_name:
            try:
                dst: PathLink = join(path.dirname, dst)
            except TypeError:
                dst: PathLink = join(dirname(
                    path.path.decode() if dst.__class__ is str
                    else path.path.encode()
                ), dst)
        func(path, dst)
        path.path = dst
        return dst
    return core


def dst2path(func: Callable) -> Closure:
    # If the destination path is instance of `Path` then convert to path link.
    @functools.wraps(func)
    def core(
            path: 'Path', dst: Union['Path', PathLink], **kw
    ) -> Union['Path', PathLink]:
        func(path, dst.path if isinstance(dst, path.__class__) else dst, **kw)
        return dst
    return core


class Path(ReadOnly):

    def __init__(
            self,
            path:            PathLink,
            /, *,
            dir_fd:          Optional[int] = None,
            follow_symlinks: bool          = True
    ):
        if path.__class__ not in (bytes, str):
            raise ge.NotAPathError(
                'path type can only be "bytes" or "str", '
                f'not "{path.__class__.__name__}".'
            )
        self.path            = path
        self.dir_fd          = dir_fd
        self.follow_symlinks = follow_symlinks

    def __str__(self) -> str:
        path = self.path
        if path.__class__ is str:
            path = '"' + path + '"'
        return f'<{__package__}.{self.__class__.__name__} path={path}>'

    __repr__ = __str__

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

    def relpath(self, start: Optional[PathLink] = None) -> PathLink:
        return relpath(self.path, start=start)

    def split(self) -> Tuple[PathLink, BytesOrStr]:
        return split(self.path)

    def splitdrive(self) -> Tuple[BytesOrStr, PathLink]:
        return splitdrive(self.path)

    @property
    def isabs(self) -> bool:
        return isabs(self.path)

    @property
    def exists(self) -> bool:
        return exists(self.path)

    @property
    def lexists(self) -> bool:
        return lexists(self.path)

    @property
    def isdir(self) -> bool:
        return isdir(self.path)

    @property
    def isfile(self) -> bool:
        return isfile(self.path)

    @property
    def islink(self) -> bool:
        return islink(self.path)

    @property
    def ismount(self) -> bool:
        return ismount(self.path)

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
    def copystat(self, dst: PathLink, /) -> None:
        copystat(self.path, dst, follow_symlinks=self.follow_symlinks)

    @dst2path
    def copymode(self, dst: PathLink, /) -> None:
        copymode(self.path, dst, follow_symlinks=self.follow_symlinks)

    @dst2path
    def symlink(self, dst: PathLink, /) -> None:
        symlink(self.path, dst, dir_fd=self.dir_fd)

    def readlink(self) -> PathLink:
        return readlink(self.path, dir_fd=self.dir_fd)

    @property
    def stat(self) -> stat_result:
        return stat(
            self.path, dir_fd=self.dir_fd, follow_symlinks=self.follow_symlinks
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
        def lchmod(self, mode: int, /) -> None:
            lchmod(self.path, mode)

        def chown(self, uid: int, gid: int) -> None:
            return chown(
                self.path, uid, gid,
                dir_fd         =self.dir_fd,
                follow_symlinks=self.follow_symlinks
            )

        def lchown(self, uid: int, gid: int) -> None:
            lchown(self.path, uid, gid)

        def chflags(self, flags: int) -> None:
            chflags(self.path, flags, follow_symlinks=self.follow_symlinks)

        def lchflags(self, flags: int) -> None:
            lchflags(self.path, flags)

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            warnings.warn(UserWarning(
                'implementation of method `chattr` is to directly call the '
                'system command `chattr`, so this is very unreliable.'
            ))
            if operator not in ('+', '-', '='):
                raise ge.ChattrError(
                    f'unsupported operation "{operator}", only "+", "-" or "=".'
                )
            c: str = f'chattr {operator}{attrs} {self.path}'
            if system(f'sudo {c} &>/dev/null'):
                raise ge.ChattrError(c)

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
                raise ge.LsattrError(c)
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

    def utime(
            self,
            /,
            times: Optional[Tuple[Union[int, float], Union[int, float]]] = None
    ) -> None:
        utime(
            self.path, times,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )


class Directory(Path):

    def __iter__(self) -> Generator:
        for name in listdir(self.path):
            path: PathLink = join(self.path, name)
            yield Directory(path) if isdir(path) else \
                File(path) if isfile(path) else Path(path)

    def listdir(self) -> List[BytesOrStr]:
        return listdir(self.path)

    def iterdir(self) -> Generator:
        return self.__iter__()

    def scandir(self) -> Iterator:
        return scandir(self.path)

    def tree(
            self,
            *,
            level:     int  = sys.getrecursionlimit(),
            fullpath:  bool = False,
            bottom_up: bool = False,
            omit_dir:  bool = False,
            packpath:  bool = False
    ) -> Generator:
        treepath: Generator = tree(
            self.path,
            level    =level,
            fullpath =fullpath,
            bottom_up=bottom_up,
            omit_dir =omit_dir
        )
        if packpath:
            for path in treepath:
                if not fullpath:
                    path: PathLink = join(self.path, path)
                yield Directory(path) if isdir(path) else \
                    File(path) if isfile(path) else Path(path)
        else:
            yield from treepath

    def walk(
            self, *, topdown: bool = True, onerror: Optional[Callable] = None
    ) -> Iterator[Tuple[PathLink, List[BytesOrStr], List[BytesOrStr]]]:
        return walk(
            self.path,
            topdown    =topdown,
            onerror    =onerror,
            followlinks=not self.follow_symlinks
        )

    def mkdir(self, mode: int = 0o777) -> None:
        mkdir(self.path, mode)

    def makedirs(self, mode: int = 0o777, *, exist_ok: bool = False) -> None:
        makedirs(self.path, mode, exist_ok=exist_ok)

    @dst2path
    def copytree(
            self,
            dst:                      Union['Directory', PathLink],
            /, *,
            symlinks:                 bool                         = False,
            ignore:                   Optional[Callable]           = None,
            copy_function:            Callable                     = copy2,
            ignore_dangling_symlinks: bool                         = False,
            dirs_exist_ok:            bool                         = False
    ) -> None:
        copytree(
            self.path, dst,
            symlinks                =symlinks,
            ignore                  =ignore,
            copy_function           =copy_function,
            ignore_dangling_symlinks=ignore_dangling_symlinks,
            dirs_exist_ok           =dirs_exist_ok
        )

    def clear(
            self,
            *,
            ignore_errors: bool               = False,
            onerror:       Optional[Callable] = None
    ) -> None:
        for name in listdir(self.path):
            path: PathLink = join(self.path, name)
            if isdir(path):
                rmtree(path, ignore_errors=ignore_errors, onerror=onerror)
            else:
                remove(path)

    def rmdir(self) -> None:
        rmdir(self.path)

    def removedirs(self) -> None:
        removedirs(self.path)

    def rmtree(
            self,
            *,
            ignore_errors: bool               = False,
            onerror:       Optional[Callable] = None
    ) -> None:
        rmtree(self.path, ignore_errors=ignore_errors, onerror=onerror)

    def chdir(self) -> None:
        chdir(self.path)


class File(Path):

    @property
    def open(self) -> 'Open':
        return Open(self)

    @property
    def content(self) -> 'Content':
        return Content(self.path)

    @content.setter
    def content(self, content: ['Content', bytes]) -> None:
        # For compatible with `Content.__iadd__` and `Content.__ior__`.
        pass

    @property
    def contents(self) -> bytes:
        return FileIO(self.path).read()

    @contents.setter
    def contents(self, content: bytes) -> None:
        if content.__class__ is not bytes:
            # Beware of original data loss due to write failures (the `content`
            # type error).
            raise TypeError(
                'content type to be written can only be "bytes", '
                f'not "{content.__class__.__name__}".'
            )
        FileIO(self.path, 'wb').write(content)

    @contents.deleter
    def contents(self) -> None:
        truncate(self.path, 0)

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitext(self.path)

    @property
    def extension(self) -> BytesOrStr:
        return splitext(self.path)[1]

    if sys.platform == 'win32':
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
    else:
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

    @dst2path
    def copy(self, dst: PathLink, /) -> None:
        copyfile(self.path, dst, follow_symlinks=self.follow_symlinks)

    def copycontent(
            self,
            other:   Union['File', FileIO],
            /, *,
            bufsize: int                   = READ_BUFFER_SIZE
    ) -> Union['File', FileIO]:
        write, read = (
            FileIO(other.path, 'wb') if isinstance(other, File) else other
        ).write, FileIO(self.path).read

        while True:
            content = read(bufsize)
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

    def truncate(self, length: int) -> None:
        truncate(self.path, length)

    def clear(self) -> None:
        truncate(self.path, 0)

    def remove(self) -> None:
        remove(self.path)

    def unlink(self) -> None:
        unlink(self.path, dir_fd=self.dir_fd)

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
        if not isinstance(file, (File, bytes, str)):
            raise ge.NotAFileError(
                f'file can only be an instance of '
                f'"{__package__}.{File.__name__}" or a path link, '
                f'not "{file.__class__.__name__}".'
            )
        self.file = file

    def __getattr__(self, mode: OpenMode) -> Closure:
        try:
            buffer: Type[BufferedIOBase] = Open.__modes__[mode]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{mode}'"
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
        return f'<{__package__}.{self.__class__.__name__} file={path}>'

    __repr__ = __str__

    @property
    def __path__(self) -> PathLink:
        return self.file.path if isinstance(self.file, File) else self.file

    def __pass__(self, buffer: Type[BufferedIOBase], mode: OpenMode) -> Closure:
        def init_buffer_instance(
                *,
                bufsize:        int                            = IO_BUFFER_SIZE,
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


class Content(Open):

    def __dir__(self) -> Iterable[str]:
        return object.__dir__(self)

    def __bytes__(self) -> bytes:
        return self.rb().read()

    def __ior__(self, content: Union['Content', bytes]) -> 'Content':
        if isinstance(content, Content):
            if abspath(content.__path__) == abspath(self.__path__):
                raise ge.IsSameFileError(
                    'source and destination cannot be the same, '
                    f'path "{abspath(self.__path__)}".'
                )
            read, write = content.rb().read, self.wb().write
            while True:
                content = read(READ_BUFFER_SIZE)
                if not content:
                    break
                write(content)
        # Beware of original data loss due to write failures (the `content` type
        # error).
        elif content.__class__ is bytes:
            self.wb().write(content)
        else:
            raise TypeError(
                'content type to be written can only be '
                f'"{__package__}.{Content.__name__}" or "bytes", '
                f'not "{content.__class__.__name__}".'
            )
        return self

    def __iadd__(self, content: Union['Content', bytes]) -> 'Content':
        if isinstance(content, Content):
            read, write = content.rb().read, self.ab().write
            while True:
                content = read(READ_BUFFER_SIZE)
                if not content:
                    break
                write(content)
        elif content.__class__ is bytes:
            self.ab().write(content)
        else:
            raise TypeError(
                'content type to be appended can only be '
                f'"{__package__}.{Content.__name__}" or "bytes", '
                f'not "{content.__class__.__name__}".'
            )
        return self

    def __eq__(self, content: Union['Content', bytes]) -> bool:
        if isinstance(content, Content):
            read1, read2 = self.rb().read, content.rb().read
            while True:
                content1 = read1(READ_BUFFER_SIZE)
                content2 = read2(READ_BUFFER_SIZE)
                if content1 == content2 == b'':
                    return True
                if content1 != content2:
                    return False
        elif content.__class__ is bytes:
            start, end = 0, READ_BUFFER_SIZE
            read1 = self.rb().read
            while True:
                content1 = read1(READ_BUFFER_SIZE)
                if content1 == content[start:end] == b'':
                    return True
                if content1 != content[start:end]:
                    return False
                start += READ_BUFFER_SIZE
                end   += READ_BUFFER_SIZE
        else:
            raise TypeError(
                'content type to be equality judgment operation can only be '
                f'"{__package__}.{Content.__name__}" or "bytes", '
                f'not "{content.__class__.__name__}".'
            )

    def __ne__(self, content: Union['Content', bytes]) -> bool:
        return not self.__eq__(content)

    def __iter__(self) -> Generator:
        return (line.rstrip(b'\r\n') for line in self.rb())

    def __len__(self) -> int:
        return getsize(self.__path__)

    def __bool__(self) -> bool:
        return bool(getsize(self.__path__))

    def read(self, size: int = -1, /) -> bytes:
        return self.rb().read(size)

    def overwrite(self, content: Union['Content', bytes], /) -> None:
        self.__ior__(content)

    def append(self, content: Union['Content', bytes]) -> None:
        self.__iadd__(content)

    def copy(
            self,
            other:   Union['Content', FileIO],
            /, *,
            bufsize: int                      = READ_BUFFER_SIZE
    ) -> None:
        write = (other.ab() if isinstance(other, Content) else other).write
        read  = self.rb().read

        while True:
            content = read(bufsize)
            if not content:
                break
            write(content)

    def truncate(self, length: int, /) -> None:
        truncate(self.__path__, length)

    def clear(self) -> None:
        truncate(self.__path__, 0)

    def md5(self, salting: bytes = b'') -> str:
        md5: HASH = openssl_md5(salting)
        read = self.rb().read

        while True:
            content = read(READ_BUFFER_SIZE)
            if not content:
                break
            md5.update(content)

        return md5.hexdigest()


def tree(
        dirpath:   PathLink,
        /, *,
        level:     int      = sys.getrecursionlimit(),
        fullpath:  bool     = False,
        bottom_up: bool     = False,
        omit_dir:  bool     = False,
        __root__=None
) -> Generator:
    root: PathLink = __root__ or dirpath

    if root.__class__ is bytes:
        sepx, null = sepb, b''
    else:
        sepx, null = sep, ''

    for name in listdir(dirpath):
        path: PathLink = join(dirpath, name)
        is_dir: bool = isdir(path)

        if bottom_up:
            if level > 1 and is_dir:
                yield from tree(
                    path,
                    level    =level - 1,
                    fullpath =fullpath,
                    bottom_up=bottom_up,
                    omit_dir =omit_dir,
                    __root__ =root
                )
            if not is_dir or not omit_dir:
                if not fullpath:
                    path: PathLink = path.replace(root + sepx, null)
                yield path
        else:
            if not is_dir or not omit_dir:
                yield path if fullpath else path.replace(root + sepx, null)
            if level > 1 and is_dir:
                yield from tree(
                    path,
                    level    =level - 1,
                    fullpath =fullpath,
                    bottom_up=bottom_up,
                    omit_dir =omit_dir,
                    __root__ =root
                )

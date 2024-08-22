"""
Copyright (c) 2022-2024 GQYLPY <http://gqylpy.com>. All rights reserved.

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
import csv
import json
import typing
import hashlib
import builtins
import warnings
import functools

from copy import copy, deepcopy
from configparser import ConfigParser

from os import (
    stat,    lstat,   stat_result,
    rename,  renames, replace,     remove,
    chmod,   access,  truncate,    utime,
    link,    symlink, unlink,      readlink,
    listdir, scandir, walk,        chdir,
    mkdir,   rmdir,   makedirs,    removedirs,
    getcwd,  getcwdb
)

if sys.platform != 'win32':
    from os import mknod, chown, system, popen

    if sys.platform == 'linux':
        try:
            from os import getxattr, setxattr, listxattr, removexattr
        except ImportError:
            def getxattr(*a, **kw): raise NotImplementedError
            setxattr = listxattr = removexattr = getxattr
    try:
        from os import lchmod, lchown, chflags, lchflags
    except ImportError:
        def lchmod(*a, **kw): raise NotImplementedError
        lchown = chflags = lchflags = lchmod
    try:
        from pwd import getpwuid
        from grp import getgrgid
    except ModuleNotFoundError:
        def getpwuid(_): raise NotImplementedError
        getgrgid = getpwuid

    READ_BUFSIZE = 1024 * 64
else:
    READ_BUFSIZE = 1024 * 1024

from os.path import (
    basename, dirname,    abspath,    realpath,   relpath,
    normpath, expanduser, expandvars,
    join,     split,      splitext,   splitdrive, sep,
    isabs,    exists,     isdir,      isfile,     islink,  ismount,
    getctime, getmtime,   getatime,   getsize
)

from shutil import move, copyfile, copytree, copystat, copymode, copy2, rmtree

from stat import (
    S_ISDIR  as s_isdir,
    S_ISREG  as s_isreg,
    S_ISBLK  as s_isblk,
    S_ISCHR  as s_ischr,
    S_ISFIFO as s_isfifo
)

from _io import (
    FileIO, BufferedReader, BufferedWriter, BufferedRandom, TextIOWrapper,
    _BufferedIOBase as BufferedIOBase,
    DEFAULT_BUFFER_SIZE
)

from typing import (
    TypeVar, Type, Final, Literal, Optional, Union, Dict, Tuple, List, Mapping,
    Callable, Iterator, Iterable, Sequence, NoReturn, Any
)

if typing.TYPE_CHECKING:
    from _typeshed import SupportsWrite
    from configparser import Interpolation

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    class Annotated(metaclass=type('', (type,), {
        '__new__': lambda *a: type.__new__(*a)()
    })):
        def __getitem__(self, *a): ...

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = TypeVar('TypeAlias')

if sys.version_info >= (3, 11):
    from typing import Self
else:
    Self = TypeVar('Self')

try:
    import yaml
except ModuleNotFoundError:
    yaml = None
else:
    YamlLoader: TypeAlias = Union[
        Type[yaml.BaseLoader],
        Type[yaml.Loader],
        Type[yaml.FullLoader],
        Type[yaml.SafeLoader],
        Type[yaml.UnsafeLoader]
    ]
    YamlDumper: TypeAlias = Union[
        Type[yaml.BaseDumper],
        Type[yaml.Dumper],
        Type[yaml.SafeDumper]
    ]

if basename(sys.argv[0]) != 'setup.py':
    import exceptionx as ex

BytesOrStr:     TypeAlias = Union[bytes, str]
PathLink:       TypeAlias = BytesOrStr
PathType:       TypeAlias = Union['Path', 'Directory', 'File', 'SystemPath']
Closure:        TypeAlias = TypeVar('Closure', bound=Callable)
CopyFunction:   TypeAlias = Callable[[PathLink, PathLink], None]
CopyTreeIgnore: TypeAlias = \
    Callable[[PathLink, List[BytesOrStr]], List[BytesOrStr]]

ConvertersMap:       TypeAlias = Dict[str, Callable[[str], Any]]
CSVDialectLike:      TypeAlias = Union[str, csv.Dialect, Type[csv.Dialect]]
JsonObjectHook:      TypeAlias = Callable[[Dict[Any, Any]], Any]
JsonObjectParse:     TypeAlias = Callable[[str], Any]
JsonObjectPairsHook: TypeAlias = Callable[[List[Tuple[Any, Any]]], Any]
FileNewline:         TypeAlias = Literal['', '\n', '\r', '\r\n']
YamlDumpStyle:       TypeAlias = Literal['|', '>', '|+', '>+']

OpenMode: TypeAlias = Annotated[Literal[
    'rb', 'rb_plus', 'rt', 'rt_plus', 'r', 'r_plus',
    'wb', 'wb_plus', 'wt', 'wt_plus', 'w', 'w_plus',
    'ab', 'ab_plus', 'at', 'at_plus', 'a', 'a_plus',
    'xb', 'xb_plus', 'xt', 'xt_plus', 'x', 'x_plus'
], 'The file open mode.']

EncodingErrorHandlingMode: TypeAlias = Annotated[Literal[
    'strict',
    'ignore',
    'replace',
    'surrogateescape',
    'xmlcharrefreplace',
    'backslashreplace',
    'namereplace'
], 'The error handling modes for encoding and decoding (strictness).']


class CSVReader(Iterator[List[str]]):
    line_num: int
    @property
    def dialect(self) -> csv.Dialect: ...
    def __next__(self) -> List[str]: ...


class CSVWriter:
    @property
    def dialect(self) -> csv.Dialect: ...
    def writerow(self, row: Iterable[Any]) -> Any: ...
    def writerows(self, rows: Iterable[Iterable[Any]]) -> None: ...


UNIQUE: Final[Annotated[object, 'A unique object.']] = object()

sepb: Final[Annotated[bytes, 'The byte type path separator.']] = sep.encode()


class MasqueradeClass(type):
    """
    Masquerade one class as another (default masquerade as first parent class).
    Warning, masquerade the class can cause unexpected problems, use caution.
    """
    __module__ = builtins.__name__

    __qualname__ = type.__qualname__
    # Warning, masquerade (modify) this attribute will cannot create the
    # portable serialized representation. In practice, however, this metaclass
    # often does not need to be serialized, so we try to ignore it.

    def __new__(mcs, __name__: str, __bases__: tuple, __dict__: dict):
        __masquerade_class__: Type[object] = __dict__.setdefault(
            '__masquerade_class__', __bases__[0] if __bases__ else object
        )

        if not isinstance(__masquerade_class__, type):
            raise TypeError('"__masquerade_class__" is not a class.')

        cls = type.__new__(
            mcs, __masquerade_class__.__name__, __bases__, __dict__
        )

        if cls.__module__ != __masquerade_class__.__module__:
            setattr(sys.modules[__masquerade_class__.__module__], __name__, cls)

        cls.__module__   = __masquerade_class__.__module__
        cls.__qualname__ = __masquerade_class__.__qualname__

        return cls

    def __hash__(cls) -> int:
        if sys._getframe(1).f_code in (deepcopy.__code__, copy.__code__):
            return type.__hash__(cls)
        return hash(cls.__masquerade_class__)

    def __eq__(cls, o) -> bool:
        return True if o is cls.__masquerade_class__ else type.__eq__(cls, o)

    def __init_subclass__(mcs) -> None:
        setattr(builtins, mcs.__name__, mcs)
        mcs.__name__     = MasqueradeClass.__name__
        mcs.__qualname__ = MasqueradeClass.__qualname__
        mcs.__module__   = MasqueradeClass.__module__


MasqueradeClass.__name__ = type.__name__
builtins.MasqueradeClass = MasqueradeClass


class ReadOnlyMode(type, metaclass=MasqueradeClass):
    # Disallow modifying the attributes of the classes externally.

    def __setattr__(cls, name: str, value: Any) -> None:
        if sys._getframe(1).f_globals['__package__'] != __package__:
            raise ex.SetAttributeError(
                f'cannot set "{name}" attribute '
                f'of immutable type "{cls.__name__}".'
            )
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name: str) -> NoReturn:
        raise ex.DeleteAttributeError(
            f'cannot delete "{name}" attribute '
            f'of immutable type "{cls.__name__}".'
        )


class ReadOnly(metaclass=ReadOnlyMode):
    # Disallow modifying the attributes of the instances externally.
    __module__ = builtins.__name__
    __qualname__ = object.__name__

    # __dict__ = {}
    # Tamper with attribute `__dict__` to avoid modifying its subclass instance
    # attribute externally, but the serious problem is that it cannot
    # deserialize its subclass instance after tampering. Stop tampering for the
    # moment, the solution is still in the works.

    def __setattr__(self, name: str, value: Any) -> None:
        if sys._getframe(1).f_globals['__name__'] != __name__ and not \
                (isinstance(self, File) and name in ('content', 'contents')):
            raise ex.SetAttributeError(
                f'cannot set "{name}" attribute in instance '
                f'of immutable type "{self.__class__.__name__}".'
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if not isinstance(self, File) or name != 'content':
            raise ex.DeleteAttributeError(
                f'cannot delete "{name}" attribute in instance '
                f'of immutable type "{self.__class__.__name__}".'
            )
        object.__delattr__(self, name)


ReadOnly.__name__ = object.__name__
builtins.ReadOnly = ReadOnly


def dst2abs(func: Callable) -> Closure:
    # If the destination path is relative and is a single name, the parent path
    # of the source is used as the parent path of the destination instead of
    # using the current working directory, different from the traditional way.
    @functools.wraps(func)
    def core(path: PathType, dst: PathLink) -> PathLink:
        try:
            singlename: bool = basename(dst) == dst
        except TypeError:
            raise ex.DestinationPathTypeError(
                'destination path type can only be "bytes" or "str", '
                f'not "{dst.__class__.__name__}".'
            ) from None
        if singlename:
            try:
                dst: PathLink = join(dirname(path), dst)
            except TypeError as e:
                if dst.__class__ is bytes:
                    name: bytes = path.name.encode()
                elif dst.__class__ is str:
                    name: str = path.name.decode()
                else:
                    raise e from None
                dst: PathLink = join(dirname(name), dst)
        func(path, dst)
        path.name = dst
        return dst
    return core


def joinpath(func: Callable) -> Closure:
    global BytesOrStr
    # Compatible with Python earlier versions.

    @functools.wraps(func)
    def core(path: PathType, name: BytesOrStr, /) -> Any:
        try:
            name: PathLink = join(path, name)
        except TypeError:
            if name.__class__ is bytes:
                name: str = name.decode()
            elif name.__class__ is str:
                name: bytes = name.encode()
            else:
                raise
            name: PathLink = join(path, name)
        return func(path, name)

    return core


def ignore_error(e) -> bool:
    return (
        getattr(e, 'errno', None) in (2, 20, 9, 10062)
                              or
        getattr(e, 'winerror', None) in (21, 123, 1921)
    )


def testpath(testfunc: Callable[[int], bool], path: PathType) -> bool:
    try:
        return testfunc(path.stat.st_mode)
    except OSError as e:
        # Path does not exist or is a broken symlink.
        if not ignore_error(e):
            raise
        return False
    except ValueError:
        # Non-encodable path.
        return False


class Path(ReadOnly):

    def __new__(cls, name: PathLink = UNIQUE, /, *, strict: bool = False, **kw):
        # Compatible object deserialization.
        if name is not UNIQUE:
            if name.__class__ not in (bytes, str):
                raise ex.NotAPathError(
                    'path type can only be "bytes" or "str", '
                    f'not "{name.__class__.__name__}".'
                )
            if strict and not exists(name):
                raise ex.SystemPathNotFoundError(
                    f'system path {name!r} does not exist.'
                )
        return object.__new__(cls)

    def __init__(
            self,
            name:            PathLink,
            /, *,
            autoabs:         bool          = False,
            strict:          bool          = False,
            dir_fd:          Optional[int] = None,
            follow_symlinks: bool          = True
    ):
        self.name            = abspath(name) if autoabs else name
        self.strict          = strict
        self.dir_fd          = dir_fd
        self.follow_symlinks = follow_symlinks

    def __str__(self) -> str:
        return self.name if self.name.__class__ is str else repr(self.name)

    def __repr__(self) -> str:
        return f'<{__package__}.{self.__class__.__name__} name={self.name!r}>'

    def __bytes__(self) -> bytes:
        return self.name if self.name.__class__ is bytes else self.name.encode()

    def __eq__(self, other: [PathType, PathLink], /) -> bool:
        if self is other:
            return True

        if isinstance(other, Path):
            other_type   = other.__class__
            other_path   = abspath(other.name)
            other_dir_fd = other.dir_fd
        elif other.__class__ in (bytes, str):
            other_type   = Path
            other_path   = abspath(other)
            other_dir_fd = None
        else:
            return False

        if self.name.__class__ is not other_path.__class__:
            other_path = other_path.encode() \
                if other_path.__class__ is str else other_path.decode()

        return any((
            self.__class__ == other_type,
            self.__class__ in (Path, SystemPath),
            other_type     in (Path, SystemPath)
        )) and abspath(self) == other_path and self.dir_fd == other_dir_fd

    def __len__(self) -> int:
        return len(self.name)

    def __bool__(self) -> bool:
        return self.exists

    def __fspath__(self) -> PathLink:
        return self.name

    def __truediv__(self, subpath: Union[PathType, PathLink], /) -> PathType:
        if isinstance(subpath, Path):
            subpath: PathLink = subpath.name
        try:
            joined_path: PathLink = join(self, subpath)
        except TypeError:
            if subpath.__class__ is bytes:
                subpath: str = subpath.decode()
            elif subpath.__class__ is str:
                subpath: bytes = subpath.encode()
            else:
                raise ex.NotAPathError(
                    'right path can only be an instance of '
                    f'"{__package__}.{Path.__name__}" or a path link, '
                    f'not "{subpath.__class__.__name__}".'
                ) from None
            joined_path: PathLink = join(self, subpath)

        if self.strict:
            if isfile(joined_path):
                pathtype = File
            elif isdir(joined_path):
                pathtype = Directory
            elif self.__class__ is Path:
                pathtype = Path
            else:
                pathtype = SystemPath
        elif self.__class__ is Path:
            pathtype = Path
        else:
            pathtype = SystemPath

        return pathtype(
            joined_path,
            strict=self.strict,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def __add__(self, subpath: Union[PathType, PathLink], /) -> PathType:
        return self.__truediv__(subpath)

    def __rtruediv__(self, dirpath: PathLink, /) -> PathType:
        try:
            joined_path: PathLink = join(dirpath, self)
        except TypeError:
            if dirpath.__class__ is bytes:
                dirpath: str = dirpath.decode()
            elif dirpath.__class__ is str:
                dirpath: bytes = dirpath.encode()
            else:
                raise ex.NotAPathError(
                    'left path type can only be "bytes" or "str", '
                    f'not "{dirpath.__class__.__name__}".'
                ) from None
            joined_path: PathLink = join(dirpath, self)
        return self.__class__(
            joined_path,
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def __radd__(self, dirpath: PathLink, /) -> PathType:
        return self.__rtruediv__(dirpath)

    @property
    def basename(self) -> BytesOrStr:
        return basename(self)

    @property
    def dirname(self) -> 'Directory':
        return Directory(
            dirname(self),
            strict=self.strict,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def dirnamel(self, level: int) -> 'Directory':
        directory = self
        for _ in range(level):
            directory: PathLink = dirname(directory)
        return Directory(
            directory,
            strict=self.strict,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def ldirname(self, *, level: int = 1) -> PathType:
        sepx: BytesOrStr = sepb if self.name.__class__ is bytes else sep
        return Directory(sepx.join(self.name.split(sepx)[level:]))

    @property
    def abspath(self) -> PathType:
        return self.__class__(
            abspath(self),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def realpath(self, *, strict: bool = False) -> PathType:
        return self.__class__(
            realpath(self, strict=strict),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def relpath(self, start: Optional[PathLink] = None) -> PathType:
        return self.__class__(
            relpath(self, start=start),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def normpath(self) -> PathType:
        return self.__class__(
            normpath(self),
            strict=self.strict,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def expanduser(self) -> PathType:
        return self.__class__(
            expanduser(self),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def expandvars(self) -> PathType:
        return self.__class__(
            expandvars(self),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def split(self) -> Tuple[PathLink, BytesOrStr]:
        return split(self)

    def splitdrive(self) -> Tuple[BytesOrStr, PathLink]:
        return splitdrive(self)

    @property
    def isabs(self) -> bool:
        return isabs(self)

    @property
    def exists(self) -> bool:
        try:
            self.stat
        except OSError as e:
            if not ignore_error(e):
                raise
            return False
        except ValueError:
            return False
        return True

    @property
    def lexists(self) -> bool:
        try:
            self.lstat
        except OSError as e:
            if not ignore_error(e):
                raise
            return False
        except ValueError:
            return False
        return True

    @property
    def isdir(self) -> bool:
        return testpath(s_isdir, self)

    @property
    def isfile(self) -> bool:
        return testpath(s_isreg, self)

    @property
    def islink(self) -> bool:
        return islink(self)

    @property
    def ismount(self) -> bool:
        return ismount(self)

    @property
    def is_block_device(self) -> bool:
        return testpath(s_isblk, self)

    @property
    def is_char_device(self) -> bool:
        return testpath(s_ischr, self)

    @property
    def isfifo(self) -> bool:
        return testpath(s_isfifo, self)

    @property
    def isempty(self) -> bool:
        if self.isdir:
            return not bool(listdir(self))
        if self.isfile:
            return not bool(getsize(self))
        if self.exists:
            raise ex.NotADirectoryOrFileError(repr(self.name))

        raise ex.SystemPathNotFoundError(
            f'system path {self.name!r} does not exist.'
        )

    @property
    def readable(self) -> bool:
        return access(
            self, 4, dir_fd=self.dir_fd, follow_symlinks=self.follow_symlinks
        )

    @property
    def writeable(self) -> bool:
        return access(
            self, 2, dir_fd=self.dir_fd, follow_symlinks=self.follow_symlinks
        )

    @property
    def executable(self) -> bool:
        return access(
            self, 1, dir_fd=self.dir_fd, follow_symlinks=self.follow_symlinks
        )

    def delete(
            self,
            *,
            ignore_errors: bool = False,
            onerror: Optional[Callable] = None
    ) -> None:
        if self.isdir:
            rmtree(self, ignore_errors=ignore_errors, onerror=onerror)
        else:
            try:
                remove(self)
            except FileNotFoundError:
                if not ignore_errors:
                    raise

    @dst2abs
    def rename(self, dst: PathLink, /) -> None:
        rename(self, dst, src_dir_fd=self.dir_fd, dst_dir_fd=self.dir_fd)

    @dst2abs
    def renames(self, dst: PathLink, /) -> None:
        renames(self, dst)

    @dst2abs
    def replace(self, dst: PathLink, /) -> None:
        replace(self, dst, src_dir_fd=self.dir_fd, dst_dir_fd=self.dir_fd)

    def move(
            self,
            dst: Union[PathType, PathLink],
            /, *,
            copy_function: Callable[[PathLink, PathLink], None] = copy2
    ) -> None:
        move(self, dst, copy_function=copy_function)

    def copystat(self, dst: Union[PathType, PathLink], /) -> None:
        copystat(self, dst, follow_symlinks=self.follow_symlinks)

    def copymode(self, dst: Union[PathType, PathLink], /) -> None:
        copymode(self, dst, follow_symlinks=self.follow_symlinks)

    def symlink(self, dst: Union[PathType, PathLink], /) -> None:
        symlink(self, dst, dir_fd=self.dir_fd)

    def readlink(self) -> PathLink:
        return readlink(self, dir_fd=self.dir_fd)

    @property
    def stat(self) -> stat_result:
        return stat(
            self, dir_fd=self.dir_fd, follow_symlinks=self.follow_symlinks
        )

    @property
    def lstat(self) -> stat_result:
        return lstat(self, dir_fd=self.dir_fd)

    def getsize(self) -> int:
        return getsize(self)

    def getctime(self) -> float:
        return getctime(self)

    def getmtime(self) -> float:
        return getmtime(self)

    def getatime(self) -> float:
        return getatime(self)

    def chmod(self, mode: int, /) -> None:
        chmod(
            self, mode, dir_fd=self.dir_fd, follow_symlinks=self.follow_symlinks
        )

    def access(self, mode: int, /, *, effective_ids: bool = False) -> bool:
        return access(
            self, mode,
            dir_fd=self.dir_fd,
            effective_ids=effective_ids,
            follow_symlinks=self.follow_symlinks
        )

    if sys.platform != 'win32':
        def lchmod(self, mode: int, /) -> None:
            lchmod(self, mode)

        @property
        def owner(self) -> str:
            return getpwuid(self.stat.st_uid).pw_name

        @property
        def group(self) -> str:
            return getgrgid(self.stat.st_gid).gr_name

        def chown(self, uid: int, gid: int) -> None:
            return chown(
                self, uid, gid,
                dir_fd=self.dir_fd,
                follow_symlinks=self.follow_symlinks
            )

        def lchown(self, uid: int, gid: int) -> None:
            lchown(self, uid, gid)

        def chflags(self, flags: int) -> None:
            chflags(self, flags, follow_symlinks=self.follow_symlinks)

        def lchflags(self, flags: int) -> None:
            lchflags(self, flags)

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            warnings.warn(
                'implementation of method `chattr` is to directly call the '
                'system command `chattr`, so this is very unreliable.'
            , stacklevel=2)
            if operator not in ('+', '-', '='):
                raise ex.ChattrError(
                    f'unsupported operation "{operator}", only "+", "-" or "=".'
                )
            pathlink: str = self.name if self.name.__class__ is str \
                else self.name.decode()
            c: str = f'chattr {operator}{attrs} {pathlink}'
            if system(f'sudo {c} &>/dev/null'):
                raise ex.ChattrError(c)

        def lsattr(self) -> str:
            warnings.warn(
                'implementation of method `lsattr` is to directly call the '
                'system command `lsattr`, so this is very unreliable.'
            , stacklevel=2)
            pathlink: str = self.name if self.name.__class__ is str \
                else self.name.decode()
            c: str = f'lsattr {pathlink}'
            attrs: str = popen(
                "sudo %s 2>/dev/null | awk '{print $1}'" % c
            ).read()[:-1]
            if len(attrs) != 16:
                raise ex.LsattrError(c)
            return attrs

        def exattr(self, attr: str, /) -> bool:
            return attr in self.lsattr()

        if sys.platform == 'linux':
            def getxattr(self, attribute: BytesOrStr, /) -> bytes:
                return getxattr(
                    self, attribute, follow_symlinks=self.follow_symlinks
                )

            def setxattr(
                    self, attribute: BytesOrStr, value: bytes, *, flags: int = 0
            ) -> None:
                setxattr(
                    self, attribute, value, flags,
                    follow_symlinks=self.follow_symlinks
                )

            def listxattr(self) -> List[str]:
                return listxattr(
                    self, follow_symlinks=self.follow_symlinks
                )

            def removexattr(self, attribute: BytesOrStr, /) -> None:
                removexattr(
                    self, attribute, follow_symlinks=self.follow_symlinks
                )

    def utime(
            self,
            /,
            times: Optional[Tuple[Union[int, float], Union[int, float]]] = None
    ) -> None:
        utime(
            self, times,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )


class Directory(Path):

    def __new__(
            cls, name: PathLink = '.', /, *, strict: bool = False, **kw
) -> 'Directory':
        instance = Path.__new__(cls, name, strict=strict, **kw)

        if strict and not isdir(name):
            raise NotADirectoryError(
                f'system path {name!r} is not a directory.'
            )

        return instance

    @joinpath
    def __getitem__(self, name: PathLink) -> PathType:
        if self.strict:
            if isdir(name):
                return Directory(name, strict=self.strict)
            if isfile(name):
                return File(name)
            if exists(name):
                return Path(name)
            raise ex.SystemPathNotFoundError(
                f'system path {name!r} does not exist.'
            )
        return SystemPath(name)

    @joinpath
    def __delitem__(self, path: PathLink) -> None:
        Path(path).delete()

    def __iter__(self) -> Iterator[Union['Directory', 'File', Path]]:
        for name in listdir(self):
            path: PathLink = join(self, name)
            yield Directory(path) if isdir(path) else \
                File(path) if isfile(path) else Path(path)

    def __bool__(self) -> bool:
        return self.isdir

    @staticmethod
    def home(
            *, strict: bool = False, follow_symlinks: bool = True
    ) -> 'Directory':
        return Directory(
            expanduser('~'), strict=strict, follow_symlinks=follow_symlinks
        )

    @property
    def subpaths(self) -> Iterator[Union['Directory', 'File', Path]]:
        return self.__iter__()

    @property
    def subpath_names(self) -> List[BytesOrStr]:
        return listdir(self)

    def scandir(self) -> Iterator:
        return scandir(self)

    def tree(
            self,
            *,
            level:      int            = float('inf'),
            downtop:    Optional[bool] = None,
            bottom_up:  bool           = UNIQUE,
            omit_dir:   bool           = False,
            pure_path:  Optional[bool] = None,
            mysophobia: bool           = UNIQUE,
            shortpath:  bool           = False
    ) -> Iterator[Union[Path, PathLink]]:
        return tree(
            self.name,
            level     =level,
            downtop   =downtop,
            bottom_up =bottom_up,
            omit_dir  =omit_dir,
            pure_path =pure_path,
            mysophobia=mysophobia,
            shortpath =shortpath
        )

    def walk(
            self, *, topdown: bool = True, onerror: Optional[Callable] = None
    ) -> Iterator[Tuple[PathLink, List[BytesOrStr], List[BytesOrStr]]]:
        return walk(
            self,
            topdown=topdown,
            onerror=onerror,
            followlinks=not self.follow_symlinks
        )

    def search(
            self,
            slicing:   BytesOrStr,
            /, *,
            level:     int            = float('inf'),
            omit_dir:  bool           = False,
            pure_path: Optional[bool] = None,
            shortpath: bool           = False
    ) -> Iterator[Union[PathType, PathLink]]:
        slicing: BytesOrStr = normpath(slicing)
        nullchar: BytesOrStr = b'' if self.name.__class__ is bytes else ''
        dirtree = tree(
            self.name, level=level, omit_dir=omit_dir,
            pure_path=pure_path, shortpath=shortpath
        )
        for subpath in dirtree:
            pure_subpath = (subpath if pure_path else subpath.name)\
                .replace(self.name, nullchar)[1:]
            try:
                r: bool = slicing in pure_subpath
            except TypeError:
                if slicing.__class__ is bytes:
                    slicing: str = slicing.decode()
                elif slicing.__class__ is str:
                    slicing: bytes = slicing.encode()
                else:
                    raise ex.ParameterError(
                        'parameter "slicing" must be of type bytes or str，'
                        f'not "{slicing.__class__.__name__}".'
                    ) from None
                r: bool = slicing in pure_subpath
            if r:
                yield subpath

    def copytree(
            self,
            dst:                      Union['Directory', PathLink],
            /, *,
            symlinks:                 bool                         = False,
            ignore:                   Optional[CopyTreeIgnore]     = None,
            copy_function:            CopyFunction                 = copy2,
            ignore_dangling_symlinks: bool                         = False,
            dirs_exist_ok:            bool                         = False
    ) -> None:
        copytree(
            self, dst,
            symlinks                =symlinks,
            ignore                  =ignore,
            copy_function           =copy_function,
            ignore_dangling_symlinks=ignore_dangling_symlinks,
            dirs_exist_ok           =dirs_exist_ok
        )

    def clear(
            self,
            *,
            ignore_errors: bool = False,
            onerror: Optional[Callable] = None
    ) -> None:
        for name in listdir(self):
            path: PathLink = join(self, name)
            if isdir(path):
                rmtree(path, ignore_errors=ignore_errors, onerror=onerror)
            else:
                try:
                    remove(self)
                except FileNotFoundError:
                    if not ignore_errors:
                        raise

    def mkdir(self, mode: int = 0o777, *, ignore_exists: bool = False) -> None:
        try:
            mkdir(self, mode)
        except FileExistsError:
            if not ignore_exists:
                raise

    def makedirs(self, mode: int = 0o777, *, exist_ok: bool = False) -> None:
        makedirs(self, mode, exist_ok=exist_ok)

    def rmdir(self) -> None:
        rmdir(self)

    def removedirs(self) -> None:
        removedirs(self)

    def rmtree(
            self,
            *,
            ignore_errors: bool = False,
            onerror: Optional[Callable] = None
    ) -> None:
        rmtree(self, ignore_errors=ignore_errors, onerror=onerror)

    @property
    def isempty(self) -> bool:
        return not bool(listdir(self))

    def chdir(self) -> None:
        chdir(self)


class File(Path):

    def __new__(cls, name: PathLink = UNIQUE, /, *, strict: bool = False, **kw):
        instance = Path.__new__(cls, name, strict=strict, **kw)

        if strict and not isfile(name):
            raise ex.NotAFileError(f'system path {name!r} is not a file.')

        return instance

    def __bool__(self) -> bool:
        return self.isfile

    def __contains__(self, subcontent: bytes, /) -> bool:
        return Content(self).contains(subcontent)

    def __iter__(self) -> Iterator[bytes]:
        yield from Content(self)

    def __truediv__(self, other: Any, /) -> NoReturn:
        x: str = __package__ + '.' + File.__name__
        y: str = other.__class__.__name__
        if hasattr(other, '__module__'):
            y: str = other.__module__ + '.' + y
        raise TypeError(f'unsupported operand type(s) for /: "{x}" and "{y}".')

    @property
    def open(self) -> 'Open':
        return Open(self)

    @property
    def ini(self) -> 'INI':
        return INI(self)

    @property
    def csv(self) -> 'CSV':
        return CSV(self)

    @property
    def json(self) -> 'JSON':
        return JSON(self)

    @property
    def yaml(self) -> 'YAML':
        return YAML(self)

    @property
    def content(self) -> bytes:
        return FileIO(self).read()

    @content.setter
    def content(self, content: bytes, /) -> None:
        if content.__class__ is not bytes:
            # Beware of original data loss due to write failures (the `content`
            # type error).
            raise TypeError(
                'content type to be written can only be "bytes", '
                f'not "{content.__class__.__name__}".'
            )
        FileIO(self, 'wb').write(content)

    @content.deleter
    def content(self) -> None:
        truncate(self, 0)

    @property
    def contents(self) -> 'Content':
        return Content(self)

    @contents.setter
    def contents(self, content: ['Content', bytes]) -> None:
        # For compatible with `Content.__iadd__` and `Content.__ior__`.
        pass

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitext(self)

    @property
    def extension(self) -> BytesOrStr:
        return splitext(self)[1]

    def copy(self, dst: Union[PathType, PathLink], /) -> None:
        copyfile(self, dst, follow_symlinks=self.follow_symlinks)

    def copycontent(
            self,
            other: Union['File', 'SupportsWrite[bytes]'],
            /, *,
            bufsize: int = READ_BUFSIZE
    ) -> Union['File', 'SupportsWrite[bytes]']:
        write, read = (
            FileIO(other, 'wb') if isinstance(other, File) else other
        ).write, FileIO(self).read

        while True:
            content = read(bufsize)
            if not content:
                break
            write(content)

        return other

    def link(self, dst: Union[PathType, PathLink], /) -> None:
        link(
            self, dst,
            src_dir_fd=self.dir_fd,
            dst_dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def isempty(self) -> bool:
        return not bool(getsize(self))

    if sys.platform == 'win32':
        def mknod(
                self,
                mode: int = 0o600,
                *,
                ignore_exists: bool = False,
                **__
        ) -> None:
            try:
                FileIO(self, 'xb')
            except FileExistsError:
                if not ignore_exists:
                    raise
            else:
                chmod(self, mode)
    else:
        def mknod(
                self,
                mode: int = None,
                *,
                device: int = 0,
                ignore_exists: bool = False
        ) -> None:
            try:
                mknod(self, mode, device, dir_fd=self.dir_fd)
            except FileExistsError:
                if not ignore_exists:
                    raise

    def mknods(
            self,
            mode: int = 0o600 if sys.platform == 'win32' else None,
            *,
            device: int = 0,
            ignore_exists: bool = False
    ) -> None:
        parentdir: PathLink = dirname(self)
        if not (parentdir in ('', b'') or exists(parentdir)):
            makedirs(parentdir, mode, exist_ok=True)
        self.mknod(mode, device=device, ignore_exists=ignore_exists)

    def remove(self, *, ignore_errors: bool = False) -> None:
        try:
            remove(self)
        except FileNotFoundError:
            if not ignore_errors:
                raise

    def unlink(self) -> None:
        unlink(self, dir_fd=self.dir_fd)

    def contains(self, subcontent: bytes, /) -> bool:
        return Content(self).contains(subcontent)

    def truncate(self, length: int) -> None:
        truncate(self, length)

    def clear(self) -> None:
        truncate(self, 0)

    def md5(self, salting: bytes = b'') -> str:
        return Content(self).md5(salting)

    def read(
            self, size: int = -1, /, *, encoding: Optional[str] = None, **kw
    ) -> str:
        return Open(self).r(encoding=encoding, **kw).read(size)

    def write(
            self, content: str, /, *, encoding: Optional[str] = None, **kw
    ) -> int:
        return Open(self).w().write(content, **kw)

    def append(
            self, content: str, /, *, encoding: Optional[str] = None, **kw
    ) -> int:
        return Open(self).a().write(content, **kw)

    create = mknod
    creates = mknods


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
            raise ex.NotAFileError(
                'file can only be an instance of '
                f'"{__package__}.{File.__name__}" or a path link, '
                f'not "{file.__class__.__name__}".'
            )
        self.file = file

    def __getattr__(self, mode: OpenMode, /) -> Closure:
        try:
            buffer: Type[BufferedIOBase] = Open.__modes__[mode]
        except KeyError:
            raise AttributeError(
                f"'{self.__class__.__name__}' object has no attribute '{mode}'"
            ) from None
        return self.__pass__(buffer, mode)

    def __dir__(self) -> Iterable[str]:
        methods = object.__dir__(self)
        methods.remove('__modes__')
        methods.remove('__pass__')
        methods += self.__modes__
        return methods

    def __repr__(self) -> str:
        filelink: PathLink = \
            self.file.name if isinstance(self.file, File) else self.file
        return f'<{__package__}.{self.__class__.__name__} file={filelink!r}>'

    def __pass__(self, buffer: Type[BufferedIOBase], mode: OpenMode) -> Closure:
        def init_buffer_instance(
                *,
                bufsize:        int                       = DEFAULT_BUFFER_SIZE,
                encoding:       Optional[str]                       = None,
                errors:         Optional[EncodingErrorHandlingMode] = None,
                newline:        Optional[str]                       = None,
                line_buffering: bool                                = False,
                write_through:  bool                                = False,
                opener:         Optional[Callable[[PathLink, int], int]] = None
        ) -> Union[BufferedIOBase, TextIOWrapper]:
            buf: BufferedIOBase = buffer(
                raw=FileIO(
                    file=self.file,
                    mode=mode.replace('_plus', '+'),
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

        init_buffer_instance.__name__ = mode
        init_buffer_instance.__qualname__ = f'{Open.__name__}.{mode}'

        return init_buffer_instance


class Content(Open):

    def __dir__(self) -> Iterable[str]:
        return object.__dir__(self)

    def __bytes__(self) -> bytes:
        return self.rb().read()

    def __ior__(self, other: Union['Content', bytes], /) -> Self:
        self.write(other)
        return self

    def __iadd__(self, other: Union['Content', bytes], /) -> Self:
        self.append(other)
        return self

    def __contains__(self, subcontent: bytes, /) -> bool:
        return self.contains(subcontent)

    def __eq__(self, other: Union['Content', bytes], /) -> bool:
        if self is other:
            return True

        if isinstance(other, Content):
            if abspath(self.file) == abspath(other.file):
                return True
            read1, read2 = self.rb().read, other.rb().read
            while True:
                content1 = read1(READ_BUFSIZE)
                content2 = read2(READ_BUFSIZE)
                if content1 == content2 == b'':
                    return True
                if content1 != content2:
                    return False

        elif other.__class__ is bytes:
            start, end = 0, READ_BUFSIZE
            read1 = self.rb().read
            while True:
                content1 = read1(READ_BUFSIZE)
                if content1 == other[start:end] == b'':
                    return True
                if content1 != other[start:end]:
                    return False
                start += READ_BUFSIZE
                end   += READ_BUFSIZE

        raise TypeError(
            'content type to be equality judgment operation can only be '
            f'"{__package__}.{Content.__name__}" or "bytes", '
            f'not "{other.__class__.__name__}".'
        )

    def __iter__(self) -> Iterator[bytes]:
        return (line.rstrip(b'\r\n') for line in self.rb())

    def __len__(self) -> int:
        return getsize(self.file)

    def __bool__(self) -> bool:
        return bool(getsize(self.file))

    def read(self, size: int = -1, /) -> bytes:
        return self.rb().read(size)

    def write(self, content: Union['Content', bytes], /) -> int:
        if isinstance(content, Content):
            if abspath(content.file) == abspath(self.file):
                raise ex.IsSameFileError(
                    'source and destination cannot be the same, '
                    f'path "{abspath(self.file)}".'
                )
            read, write, count = content.rb().read, self.wb().write, 0
            while True:
                content = read(READ_BUFSIZE)
                if not content:
                    break
                count += write(content)
        # Beware of original data loss due to write failures (the `content` type
        # error).
        elif content.__class__ is bytes:
            count = self.wb().write(content)
        else:
            raise TypeError(
                'content type to be written can only be '
                f'"{__package__}.{Content.__name__}" or "bytes", '
                f'not "{content.__class__.__name__}".'
            )
        return count

    def append(self, content: Union['Content', bytes], /) -> int:
        if isinstance(content, Content):
            read, write, count = content.rb().read, self.ab().write, 0
            while True:
                content = read(READ_BUFSIZE)
                if not content:
                    break
                count += write(content)
        elif content.__class__ is bytes:
            count = self.ab().write(content)
        else:
            raise TypeError(
                'content type to be appended can only be '
                f'"{__package__}.{Content.__name__}" or "bytes", '
                f'not "{content.__class__.__name__}".'
            )
        return count

    def contains(self, subcontent: bytes, /) -> bool:
        if subcontent == b'':
            return True

        deviation_index = -len(subcontent) + 1
        deviation_value = b''

        read = self.rb().read

        while True:
            content = read(READ_BUFSIZE)
            if not content:
                return False
            if subcontent in deviation_value + content:
                return True
            deviation_value = content[deviation_index:]

    def copy(
            self,
            other: Union['Content', 'SupportsWrite[bytes]'],
            /, *,
            bufsize: int = READ_BUFSIZE
    ) -> None:
        write = (other.ab() if isinstance(other, Content) else other).write
        read = self.rb().read

        while True:
            content = read(bufsize)
            if not content:
                break
            write(content)

    def truncate(self, length: int, /) -> None:
        truncate(self.file, length)

    def clear(self) -> None:
        truncate(self.file, 0)

    def md5(self, salting: bytes = b'') -> str:
        md5 = hashlib.md5(salting)
        read = self.rb().read

        while True:
            content = read(READ_BUFSIZE)
            if not content:
                break
            md5.update(content)

        return md5.hexdigest()

    overwrite = write


class tree:

    def __init__(
            self,
            dirpath:    Optional[PathLink] = None,
            /, *,
            level:      int                = float('inf'),
            downtop:    Optional[bool]     = None,
            bottom_up:  bool               = UNIQUE,
            omit_dir:   bool               = False,
            pure_path:  Optional[bool]     = None,
            mysophobia: bool               = UNIQUE,
            shortpath:  bool               = False
    ):
        if dirpath == b'':
            dirpath: bytes = getcwdb()
        elif dirpath in (None, ''):
            dirpath: str = getcwd()

        self.root = dirpath

        if bottom_up is not UNIQUE:
            warnings.warn(
                'parameter "bottom_up" will be deprecated soon, replaced to '
                '"downtop".', stacklevel=2
            )
            if downtop is None:
                downtop = bottom_up

        self.tree = (
            self.downtop if downtop else self.topdown
        )(dirpath, level=level)

        self.omit_dir = omit_dir

        if mysophobia is not UNIQUE:
            warnings.warn(
                'parameter "mysophobia" will be deprecated soon, replaced to '
                '"pure_path".', stacklevel=2
            )
            if pure_path is None:
                pure_path = mysophobia

        self.pure_path = pure_path
        self.shortpath = shortpath

        if self.pure_path and shortpath:
            self.nullchar = b'' if dirpath.__class__ is bytes else ''

    def __iter__(self) -> Iterator[Union[Path, PathLink]]:
        return self

    def __next__(self) -> Union[Path, PathLink]:
        return next(self.tree)

    def topdown(
            self, dirpath: PathLink, /, *, level: int
    ) -> Iterator[Union[Path, PathLink]]:
        for name in listdir(dirpath):
            path: PathLink = join(dirpath, name)
            is_dir: bool = isdir(path)
            if not (is_dir and self.omit_dir):
                yield self.path(path, is_dir=is_dir)
            if level > 1 and is_dir:
                yield from self.topdown(path, level=level - 1)

    def downtop(
            self, dirpath: PathLink, /, *, level: int
    ) -> Iterator[Union[Path, PathLink]]:
        for name in listdir(dirpath):
            path: PathLink = join(dirpath, name)
            is_dir: bool = isdir(path)
            if level > 1 and is_dir:
                yield from self.downtop(path, level=level - 1)
            if not (is_dir and self.omit_dir):
                yield self.path(path, is_dir=is_dir)

    def path(
            self, path: PathLink, /, *, is_dir: bool
    ) -> Union[Path, PathLink]:
        if self.pure_path:
            return self.basepath(path) if self.shortpath else path
        elif is_dir:
            return Directory(path)
        elif isfile(path):
            return File(path)
        else:
            return Path(path)

    def basepath(self, path: PathLink, /) -> PathLink:
        path: PathLink = path.replace(self.root, self.nullchar)
        if path[0] in (47, 92, '/', '\\'):
            path: PathLink = path[1:]
        return path


class INI:
    def __init__(self, file: File, /):
        self.file = file

    def read(
            self,
            encoding:                Optional[str]               = None,
            *,
            defaults:                Optional[Mapping[str, str]] = None,
            dict_type:               Type[Mapping[str, str]]     = dict,
            allow_no_value:          bool                        = False,
            delimiters:              Sequence[str]               = ('=', ':'),
            comment_prefixes:        Sequence[str]               = ('#', ';'),
            inline_comment_prefixes: Optional[Sequence[str]]     = None,
            strict:                  bool                        = True,
            empty_lines_in_values:   bool                        = True,
            default_section:         str                         = 'DEFAULT',
            interpolation:           Optional['Interpolation']   = None,
            converters:              Optional[ConvertersMap]     = None
    ) -> ConfigParser:
        kw = {}
        if interpolation is not None:
            kw['interpolation'] = interpolation
        if converters is not None:
            kw['converters'] = converters
        config = ConfigParser(
            defaults               =defaults,
            dict_type              =dict_type,
            allow_no_value         =allow_no_value,
            delimiters             =delimiters,
            comment_prefixes       =comment_prefixes,
            inline_comment_prefixes=inline_comment_prefixes,
            strict                 =strict,
            empty_lines_in_values  =empty_lines_in_values,
            default_section        =default_section,
            **kw
        )
        config.read(self.file, encoding=encoding)
        return config


class CSV:

    def __init__(self, file: File, /):
        self.file = file

    def reader(
            self,
            dialect:          CSVDialectLike = 'excel',
            *,
            delimiter:        str            = ',',
            quotechar:        Optional[str]  = '"',
            escapechar:       Optional[str]  = None,
            doublequote:      bool           = True,
            skipinitialspace: bool           = False,
            lineterminator:   str            = '\r\n',
            quoting:          int            = 0,
            strict:           bool           = False
    ) -> CSVReader:
        return csv.reader(
            Open(self.file).r(newline=''), dialect,
            delimiter       =delimiter,
            quotechar       =quotechar,
            escapechar      =escapechar,
            doublequote     =doublequote,
            skipinitialspace=skipinitialspace,
            lineterminator  =lineterminator,
            quoting         =quoting,
            strict          =strict
        )

    def writer(
            self,
            dialect:          CSVDialectLike    = 'excel',
            *,
            mode:             Literal['w', 'a'] = 'w',
            encoding:         Optional[str]     = None,
            delimiter:        str               = ',',
            quotechar:        Optional[str]     = '"',
            escapechar:       Optional[str]     = None,
            doublequote:      bool              = True,
            skipinitialspace: bool              = False,
            lineterminator:   str               = '\r\n',
            quoting:          int               = 0,
            strict:           bool              = False
    ) -> CSVWriter:
        if mode not in ('w', 'a'):
            raise ex.ParameterError(
                f'parameter "mode" must be "w" or "a", not {mode!r}.'
            )
        return csv.writer(
            getattr(Open(self.file), mode)(encoding=encoding, newline=''),
            dialect,
            delimiter       =delimiter,
            quotechar       =quotechar,
            escapechar      =escapechar,
            doublequote     =doublequote,
            skipinitialspace=skipinitialspace,
            lineterminator  =lineterminator,
            quoting         =quoting,
            strict          =strict
        )


class JSON:

    def __init__(self, file: File, /):
        self.file = file

    def load(
            self,
            *,
            cls:               Type[json.JSONDecoder]        = json.JSONDecoder,
            object_hook:       Optional[JsonObjectHook]      = None,
            parse_float:       Optional[JsonObjectParse]     = None,
            parse_int:         Optional[JsonObjectParse]     = None,
            parse_constant:    Optional[JsonObjectParse]     = None,
            object_pairs_hook: Optional[JsonObjectPairsHook] = None
    ) -> Any:
        return json.loads(
            self.file.content,
            cls              =cls,
            object_hook      =object_hook,
            parse_float      =parse_float,
            parse_int        =parse_int,
            parse_constant   =parse_constant,
            object_pairs_hook=object_pairs_hook
        )

    def dump(
            self,
            obj:            Any,
            *,
            skipkeys:       bool                           = False,
            ensure_ascii:   bool                           = True,
            check_circular: bool                           = True,
            allow_nan:      bool                           = True,
            cls:            Type[json.JSONEncoder]         = json.JSONEncoder,
            indent:         Optional[Union[int, str]]      = None,
            separators:     Optional[Tuple[str, str]]      = None,
            default:        Optional[Callable[[Any], Any]] = None,
            sort_keys:      bool                           = False,
            **kw
    ) -> None:
        return json.dump(
            obj, Open(self.file).w(),
            skipkeys      =skipkeys,
            ensure_ascii  =ensure_ascii,
            check_circular=check_circular,
            allow_nan     =allow_nan,
            cls           =cls,
            indent        =indent,
            separators    =separators,
            default       =default,
            sort_keys     =sort_keys,
            **kw
        )


class YAML:

    def __init__(self, file: File, /):
        if yaml is None:
            raise ModuleNotFoundError(
                'dependency has not been installed, '
                'run `pip3 install systempath[pyyaml]`.'
            )
        self.file = file

    def load(self, loader: Optional['YamlLoader'] = None) -> Any:
        return yaml.load(FileIO(self.file), loader or yaml.SafeLoader)

    def load_all(self, loader: Optional['YamlLoader'] = None) -> Iterator[Any]:
        return yaml.load_all(FileIO(self.file), loader or yaml.SafeLoader)

    def dump(
            self,
            data:               Any,
            /,
            dumper:             Optional['YamlDumper']      = None,
            *,
            default_style:      Optional[str]               = None,
            default_flow_style: bool                        = False,
            canonical:          Optional[bool]              = None,
            indent:             Optional[int]               = None,
            width:              Optional[int]               = None,
            allow_unicode:      Optional[bool]              = None,
            line_break:         Optional[str]               = None,
            encoding:           Optional[str]               = None,
            explicit_start:     Optional[bool]              = None,
            explicit_end:       Optional[bool]              = None,
            version:            Optional[Tuple[int, int]]   = None,
            tags:               Optional[Mapping[str, str]] = None,
            sort_keys:          bool                        = True
    ) -> None:
        return yaml.dump_all(
            [data], Open(self.file).w(), dumper or yaml.Dumper,
            default_style     =default_style,
            default_flow_style=default_flow_style,
            canonical         =canonical,
            indent            =indent,
            width             =width,
            allow_unicode     =allow_unicode,
            line_break        =line_break,
            encoding          =encoding,
            explicit_start    =explicit_start,
            explicit_end      =explicit_end,
            version           =version,
            tags              =tags,
            sort_keys         =sort_keys
        )

    def dump_all(
            self,
            documents:          Iterable[Any],
            /,
            dumper:             Optional['YamlLoader']      = None,
            *,
            default_style:      Optional[YamlDumpStyle]     = None,
            default_flow_style: bool                        = False,
            canonical:          Optional[bool]              = None,
            indent:             Optional[int]               = None,
            width:              Optional[int]               = None,
            allow_unicode:      Optional[bool]              = None,
            line_break:         Optional[FileNewline]       = None,
            encoding:           Optional[str]               = None,
            explicit_start:     Optional[bool]              = None,
            explicit_end:       Optional[bool]              = None,
            version:            Optional[Tuple[int, int]]   = None,
            tags:               Optional[Mapping[str, str]] = None,
            sort_keys:          bool                        = True
    ) -> None:
        return yaml.dump_all(
            documents, Open(self.file).w(), dumper or yaml.Dumper,
            default_style     =default_style,
            default_flow_style=default_flow_style,
            canonical         =canonical,
            indent            =indent,
            width             =width,
            allow_unicode     =allow_unicode,
            line_break        =line_break,
            encoding          =encoding,
            explicit_start    =explicit_start,
            explicit_end      =explicit_end,
            version           =version,
            tags              =tags,
            sort_keys         =sort_keys
        )


class SystemPath(Directory, File):

    def __init__(
            self,
            root:            PathLink      = '.',
            /, *,
            autoabs:         bool          = False,
            strict:          bool          = False,
            dir_fd:          Optional[int] = None,
            follow_symlinks: bool          = True
    ):
        Path.__init__(
            self,
            '.' if root == '' else b'.' if root == b'' else root,
            autoabs        =autoabs,
            strict         =strict,
            dir_fd         =dir_fd,
            follow_symlinks=follow_symlinks
        )

    __new__     = Path.__new__
    __bool__    = Path.__bool__
    __truediv__ = Path.__truediv__

    isempty = Path.isempty

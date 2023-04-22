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

    __read_bufsize__ = 1024 * 64
else:
    __read_bufsize__ = 1024 * 1024

from os.path import (
    basename, dirname,    abspath,  realpath,   relpath,
    normpath, expanduser, expandvars,
    join,     split,      splitext, splitdrive,
    isabs,    exists,     isdir,    isfile,     islink,  ismount,
    getctime, getmtime,   getatime, getsize
)

from shutil import move, copyfile, copytree, copystat, copymode, copy2, rmtree

from pathlib import _ignore_error

from stat import S_ISDIR, S_ISREG, S_ISBLK, S_ISCHR, S_ISFIFO

from _io import (
    FileIO, BufferedReader, BufferedWriter, BufferedRandom, TextIOWrapper,
    _BufferedIOBase     as BufferedIOBase,
    DEFAULT_BUFFER_SIZE as __io_bufsize__
)

from hashlib import md5

from typing import (
    TypeVar, Type, Literal, Optional, Union, Tuple, List, Final, Callable,
    Generator, Iterator, Iterable, NoReturn, Any
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

__unique__: Final = object()


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
            ) from None

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
        return True if o is cls.__masquerade_class__ else type.__eq__(cls, o)


class ReadOnlyMode(type, metaclass=MasqueradeClass):
    # Disallow modifying the attributes of the classes externally.
    __masquerade_class__ = type

    def __setattr__(cls, name: str, value: Any) -> None:
        if sys._getframe().f_back.f_globals['__package__'] != __package__:
            raise ge.SetAttributeError(
                f'cannot set "{name}" attribute '
                f'of immutable type "{cls.__name__}".'
            )
        type.__setattr__(cls, name, value)

    def __delattr__(cls, name: str) -> NoReturn:
        raise ge.DeleteAttributeError(
            f'cannot execute operation to delete attribute '
            f'of immutable type "{cls.__name__}".'
        )


class ReadOnly(metaclass=ReadOnlyMode):
    # Disallow modifying the attributes of the instances externally.

    # __dict__ = {}
    # Tamper with attribute `__dict__` to avoid modifying its subclass instance
    # attribute externally, but the serious problem is that it cannot
    # deserialize its subclass instance after tampering. Stop tampering for the
    # moment, the solution is still in the works.

    def __setattr__(self, name: str, value: Any) -> None:
        if sys._getframe().f_back.f_globals['__name__'] != __name__ and not \
                (isinstance(self, File) and name in ('content', 'contents')):
            raise ge.SetAttributeError(
                f'cannot set "{name}" attribute in instance '
                f'of immutable type "{self.__class__.__name__}".'
            )
        object.__setattr__(self, name, value)

    def __delattr__(self, name: str) -> None:
        if not isinstance(self, File) or name != 'content':
            raise ge.DeleteAttributeError(
                f'cannot execute operation to delete attribute in instance '
                f'of immutable type "{File.__name__}".'
            )
        object.__delattr__(self, name)


def dst2abs(func: Callable) -> Closure:
    # If the destination path is relative and is a single name, the parent path
    # of the source is used as the parent path of the destination instead of
    # using the current working directory, different from the traditional way.
    @functools.wraps(func)
    def core(path: 'Path', dst: PathLink) -> PathLink:
        try:
            singlename: bool = basename(dst) == dst
        except TypeError:
            raise ge.DestinationPathTypeError(
                'destination path type can only be "bytes" or "str", '
                f'not "{dst.__class__.__name__}".'
            ) from None
        if singlename:
            try:
                dst: PathLink = join(dirname(path.name), dst)
            except TypeError:
                dst: PathLink = join(dirname(
                    path.name.decode() if dst.__class__ is str
                    else path.name.encode()
                ), dst)
        func(path, dst)
        path.name = dst
        return dst
    return core


def dst2path(func: Callable) -> Closure:
    # If the destination path is instance of `Path` then convert to path link.
    @functools.wraps(func)
    def core(
            path: 'Path', dst: Union['Path', PathLink], **kw
    ) -> Union['Path', PathLink]:
        func(path, dst.name if isinstance(dst, path.__class__) else dst, **kw)
        return dst
    return core


def joinpath(func: Callable) -> Closure:
    global BytesOrStr
    # Compatible with Python earlier versions.

    @functools.wraps(func)
    def core(path: 'Path', name: BytesOrStr, /) -> Any:
        try:
            name: PathLink = join(path.name, name)
        except TypeError:
            if name.__class__ is bytes:
                name: str = name.decode()
            elif name.__class__ is str:
                name: bytes = name.encode()
            else:
                raise
            name: PathLink = join(path.name, name)
        return func(path, name)

    return core


def testpath(testfunc: Callable[[int], bool], path: 'Path') -> bool:
    try:
        return testfunc(path.stat.st_mode)
    except OSError as e:
        # Path does not exist or is a broken symlink.
        if not _ignore_error(e):
            raise
        return False
    except ValueError:
        # Non-encodable path
        return False


class Path(ReadOnly):

    def __new__(
            cls, name: PathLink = __unique__, /, strict: bool = False, **kw
    ):
        # Compatible object deserialization.
        if name is not __unique__:
            if name.__class__ not in (bytes, str):
                raise ge.NotAPathError(
                    'path type can only be "bytes" or "str", '
                    f'not "{name.__class__.__name__}".'
                )
            if strict and not exists(name):
                raise ge.SystemPathNotFoundError(
                    f'system path {repr(name)} does not exist.'
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
        return f'<{__package__}.{self.__class__.__name__} ' \
               f'name={repr(self.name)}>'

    def __bytes__(self) -> bytes:
        return self.name if self.name.__class__ is bytes else self.name.encode()

    def __eq__(self, other: ['Path', PathLink], /) -> bool:
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
        )) and abspath(self.name) == other_path and self.dir_fd == other_dir_fd

    @property
    def basename(self) -> BytesOrStr:
        return basename(self.name)

    @property
    def dirname(self) -> 'Directory':
        return Directory(
            dirname(self.name),
            strict         =self.strict,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def dirnamel(self, level: int) -> 'Directory':
        directory: PathLink = self.name
        for _ in range(level):
            directory: PathLink = dirname(directory)
        return Directory(
            directory,
            strict         =self.strict,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def abspath(self) -> 'Path':
        return self.__class__(
            abspath(self.name),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def realpath(self, *, strict: bool = False) -> 'Path':
        return self.__class__(
            realpath(self.name, strict=strict),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def relpath(self, start: Optional[PathLink] = None) -> 'Path':
        return self.__class__(
            relpath(self.name, start=start),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def normpath(self) -> 'Path':
        return self.__class__(
            normpath(self.name),
            strict         =self.strict,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def expanduser(self) -> 'Path':
        return self.__class__(
            expanduser(self.name),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def expandvars(self) -> 'Path':
        return self.__class__(
            expandvars(self.name),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def split(self) -> Tuple[PathLink, BytesOrStr]:
        return split(self.name)

    def splitdrive(self) -> Tuple[BytesOrStr, PathLink]:
        return splitdrive(self.name)

    @property
    def isabs(self) -> bool:
        return isabs(self.name)

    @property
    def exists(self) -> bool:
        try:
            self.stat
        except OSError as e:
            if not _ignore_error(e):
                raise
            return False
        except ValueError:
            return False
        return True

    @property
    def lexists(self) -> bool:
        try:
            stat(self.name, dir_fd=self.dir_fd, follow_symlinks=False)
        except OSError as e:
            if not _ignore_error(e):
                raise
            return False
        except ValueError:
            return False
        return True

    @property
    def isdir(self) -> bool:
        return testpath(S_ISDIR, self)

    @property
    def isfile(self) -> bool:
        return testpath(S_ISREG, self)

    @property
    def islink(self) -> bool:
        return islink(self.name)

    @property
    def ismount(self) -> bool:
        return ismount(self.name)

    @property
    def is_block_device(self) -> bool:
        return testpath(S_ISBLK, self)

    @property
    def is_char_device(self) -> bool:
        return testpath(S_ISCHR, self)

    @property
    def isfifo(self) -> bool:
        return testpath(S_ISFIFO, self)

    @property
    def readable(self) -> bool:
        return access(
            self.name, 4,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def writeable(self) -> bool:
        return access(
            self.name, 2,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def executable(self) -> bool:
        return access(
            self.name, 1,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def delete(
            self,
            *,
            ignore_errors: bool               = False,
            onerror:       Optional[Callable] = None
    ) -> None:
        if self.isdir:
            rmtree(self.name, ignore_errors=ignore_errors, onerror=onerror)
        else:
            try:
                remove(self.name)
            except FileNotFoundError:
                if not ignore_errors:
                    raise

    @dst2abs
    def rename(self, dst: PathLink, /) -> None:
        rename(self.name, dst, src_dir_fd=self.dir_fd, dst_dir_fd=self.dir_fd)

    @dst2abs
    def renames(self, dst: PathLink, /) -> None:
        renames(self.name, dst)

    @dst2abs
    def replace(self, dst: PathLink, /) -> None:
        replace(self.name, dst, src_dir_fd=self.dir_fd, dst_dir_fd=self.dir_fd)

    @dst2path
    def move(
            self,
            dst:           PathLink,
            /, *,
            copy_function: Callable[[PathLink, PathLink], None] = copy2
    ) -> None:
        move(self.name, dst, copy_function=copy_function)

    @dst2path
    def copystat(self, dst: PathLink, /) -> None:
        copystat(self.name, dst, follow_symlinks=self.follow_symlinks)

    @dst2path
    def copymode(self, dst: PathLink, /) -> None:
        copymode(self.name, dst, follow_symlinks=self.follow_symlinks)

    @dst2path
    def symlink(self, dst: PathLink, /) -> None:
        symlink(self.name, dst, dir_fd=self.dir_fd)

    def readlink(self) -> PathLink:
        return readlink(self.name, dir_fd=self.dir_fd)

    @property
    def stat(self) -> stat_result:
        return stat(
            self.name, dir_fd=self.dir_fd, follow_symlinks=self.follow_symlinks
        )

    @property
    def lstat(self) -> stat_result:
        return lstat(self.name, dir_fd=self.dir_fd)

    def getsize(self) -> int:
        return getsize(self.name)

    def getctime(self) -> float:
        return getctime(self.name)

    def getmtime(self) -> float:
        return getmtime(self.name)

    def getatime(self) -> float:
        return getatime(self.name)

    def chmod(self, mode: int, /) -> None:
        chmod(
            self.name, mode,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def access(self, mode: int, /, *, effective_ids: bool = False) -> bool:
        return access(
            self.name, mode,
            dir_fd         =self.dir_fd,
            effective_ids  =effective_ids,
            follow_symlinks=self.follow_symlinks
        )

    if sys.platform != 'win32':
        def lchmod(self, mode: int, /) -> None:
            lchmod(self.name, mode)

        @property
        def owner(self) -> str:
            return getpwuid(self.stat.st_uid).pw_name

        @property
        def group(self) -> str:
            return getgrgid(self.stat.st_gid).gr_name

        def chown(self, uid: int, gid: int) -> None:
            return chown(
                self.name, uid, gid,
                dir_fd         =self.dir_fd,
                follow_symlinks=self.follow_symlinks
            )

        def lchown(self, uid: int, gid: int) -> None:
            lchown(self.name, uid, gid)

        def chflags(self, flags: int) -> None:
            chflags(self.name, flags, follow_symlinks=self.follow_symlinks)

        def lchflags(self, flags: int) -> None:
            lchflags(self.name, flags)

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            warnings.warn(
                'implementation of method `chattr` is to directly call the '
                'system command `chattr`, so this is very unreliable.'
            , stacklevel=2)
            if operator not in ('+', '-', '='):
                raise ge.ChattrError(
                    f'unsupported operation "{operator}", only "+", "-" or "=".'
                )
            c: str = f'chattr {operator}{attrs} {self.name}'
            if system(f'sudo {c} &>/dev/null'):
                raise ge.ChattrError(c)

        def lsattr(self) -> str:
            warnings.warn(
                'implementation of method `lsattr` is to directly call the '
                'system command `lsattr`, so this is very unreliable.'
            , stacklevel=2)
            c: str = f'lsattr {self.name}'
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
                    self.name, attribute,
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
                    self.name, attribute, value, flags,
                    follow_symlinks=self.follow_symlinks
                )

            def listxattr(self) -> List[str]:
                return listxattr(
                    self.name, follow_symlinks=self.follow_symlinks
                )

            def removexattr(self, attribute: BytesOrStr, /) -> None:
                removexattr(
                    self.name, attribute, follow_symlinks=self.follow_symlinks
                )

    def utime(
            self,
            /,
            times: Optional[Tuple[Union[int, float], Union[int, float]]] = None
    ) -> None:
        utime(
            self.name, times,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )


class Directory(Path):

    def __new__(cls, name: PathLink = '.', /, strict: bool = False, **kw):
        instance = Path.__new__(cls, name, strict=strict, **kw)

        if strict and not isdir(name):
            raise NotADirectoryError(
                f'system path {repr(name)} is not a directory.'
            )

        return instance

    @joinpath
    def __getitem__(
            self, name: PathLink
    ) -> Union['SystemPath', 'Directory', 'File', Path]:
        if self.strict:
            if isdir(name):
                return Directory(name, strict=self.strict)
            if isfile(name):
                return File(name)
            if exists(name):
                return Path(name)
            else:
                raise ge.SystemPathNotFoundError(
                    f'system path {repr(name)} does not exist.'
                )
        else:
            return SystemPath(name)

    @joinpath
    def __delitem__(self, path: PathLink) -> None:
        Path(path).delete()

    def __iter__(self) -> Generator:
        for name in listdir(self.name):
            path: PathLink = join(self.name, name)
            yield Directory(path) if isdir(path) else \
                File(path) if isfile(path) else Path(path)

    @staticmethod
    def home(
            *, strict: bool = False, follow_symlinks: bool = True
    ) -> 'Directory':
        return Directory(
            expanduser('~'), strict=strict, follow_symlinks=follow_symlinks
        )

    @property
    def subpaths(self) -> Generator:
        return self.__iter__()

    @property
    def subpath_names(self) -> List[BytesOrStr]:
        return listdir(self.name)

    def scandir(self) -> Iterator:
        return scandir(self.name)

    def tree(
            self,
            *,
            level:      int  = sys.getrecursionlimit(),
            bottom_up:  bool = False,
            omit_dir:   bool = False,
            mysophobia: bool = False,
            shortpath:  bool = False
    ) -> Generator:
        return tree(
            self.name,
            level     =level,
            bottom_up =bottom_up,
            omit_dir  =omit_dir,
            mysophobia=mysophobia,
            shortpath =shortpath
        )

    def walk(
            self, *, topdown: bool = True, onerror: Optional[Callable] = None
    ) -> Iterator[Tuple[PathLink, List[BytesOrStr], List[BytesOrStr]]]:
        return walk(
            self.name,
            topdown    =topdown,
            onerror    =onerror,
            followlinks=not self.follow_symlinks
        )

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
            self.name, dst,
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
        for name in listdir(self.name):
            path: PathLink = join(self.name, name)
            if isdir(path):
                rmtree(path, ignore_errors=ignore_errors, onerror=onerror)
            else:
                remove(path)

    def mkdir(self, mode: int = 0o777, *, ignore_exists: bool = False) -> None:
        try:
            mkdir(self.name, mode)
        except FileExistsError:
            if not ignore_exists:
                raise

    def makedirs(self, mode: int = 0o777, *, exist_ok: bool = False) -> None:
        makedirs(self.name, mode, exist_ok=exist_ok)

    def rmdir(self) -> None:
        rmdir(self.name)

    def removedirs(self) -> None:
        removedirs(self.name)

    def rmtree(
            self,
            *,
            ignore_errors: bool               = False,
            onerror:       Optional[Callable] = None
    ) -> None:
        rmtree(self.name, ignore_errors=ignore_errors, onerror=onerror)

    def chdir(self) -> None:
        chdir(self.name)


class File(Path):

    def __new__(
            cls, name: PathLink = __unique__, /, strict: bool = False, **kw
    ):
        instance = Path.__new__(cls, name, strict=strict, **kw)

        if strict and not isfile(name):
            raise ge.NotAFileError(f'system path {repr(name)} is not a file.')

        return instance

    @property
    def open(self) -> 'Open':
        return Open(self)

    @property
    def content(self) -> bytes:
        return FileIO(self.name).read()

    @content.setter
    def content(self, content: bytes) -> None:
        if content.__class__ is not bytes:
            # Beware of original data loss due to write failures (the `content`
            # type error).
            raise TypeError(
                'content type to be written can only be "bytes", '
                f'not "{content.__class__.__name__}".'
            )
        FileIO(self.name, 'wb').write(content)

    @content.deleter
    def content(self) -> None:
        truncate(self.name, 0)

    @property
    def contents(self) -> 'Content':
        return Content(self.name)

    @contents.setter
    def contents(self, content: ['Content', bytes]) -> None:
        # For compatible with `Content.__iadd__` and `Content.__ior__`.
        pass

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return splitext(self.name)

    @property
    def extension(self) -> BytesOrStr:
        return splitext(self.name)[1]

    @dst2path
    def copy(self, dst: PathLink, /) -> None:
        copyfile(self.name, dst, follow_symlinks=self.follow_symlinks)

    def copycontent(
            self,
            other:   Union['File', FileIO],
            /, *,
            bufsize: int                   = __read_bufsize__
    ) -> Union['File', FileIO]:
        write, read = (
            FileIO(other.name, 'wb') if isinstance(other, File) else other
        ).write, FileIO(self.name).read

        while True:
            content = read(bufsize)
            if not content:
                break
            write(content)

        return other

    @dst2path
    def link(self, dst: PathLink, /) -> None:
        link(
            self.name, dst,
            src_dir_fd     =self.dir_fd,
            dst_dir_fd     =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def truncate(self, length: int) -> None:
        truncate(self.name, length)

    def clear(self) -> None:
        truncate(self.name, 0)

    if sys.platform == 'win32':
        def mknod(
                self,
                mode:          int  = 0o600,
                *,
                ignore_exists: bool = False,
                **__
        ) -> None:
            try:
                FileIO(self.name, 'xb')
            except FileExistsError:
                if not ignore_exists:
                    raise
            else:
                chmod(self.name, mode)
    else:
        def mknod(
                self,
                mode:          int  = None,
                *,
                device:        int  = 0,
                ignore_exists: bool = False
        ) -> None:
            try:
                mknod(self.name, mode, device, dir_fd=self.dir_fd)
            except FileExistsError:
                if not ignore_exists:
                    raise

    def mknods(
            self,
            mode:          int  = 0o600 if sys.platform == 'win32' else None,
            *,
            device:        int  = 0,
            ignore_exists: bool = False
    ) -> None:
        parentdir: PathLink = dirname(self.name)
        if not (parentdir in ('', b'') or exists(parentdir)):
            makedirs(parentdir, mode, exist_ok=True)
        self.mknod(mode, device=device, ignore_exists=ignore_exists)

    def remove(self, *, ignore_errors: bool = False) -> None:
        try:
            remove(self.name)
        except FileNotFoundError:
            if not ignore_errors:
                raise

    def unlink(self) -> None:
        unlink(self.name, dir_fd=self.dir_fd)

    def md5(self, salting: bytes = b'') -> str:
        m5 = md5(salting)
        read = FileIO(self.name).read

        while True:
            content = read(__read_bufsize__)
            if not content:
                break
            m5.update(content)

        return m5.hexdigest()


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
            ) from None
        return self.__pass__(buffer, mode)

    def __dir__(self) -> Iterable[str]:
        methods = object.__dir__(self)
        methods.remove('__modes__')
        methods.remove('__pass__')
        methods.remove('__path__')
        methods += self.__modes__
        return methods

    def __str__(self) -> str:
        return f'<{__package__}.{self.__class__.__name__} ' \
               f'file={repr(self.__path__)}>'

    __repr__ = __str__

    @property
    def __path__(self) -> PathLink:
        return self.file.name if isinstance(self.file, File) else self.file

    def __pass__(self, buffer: Type[BufferedIOBase], mode: OpenMode) -> Closure:
        def init_buffer_instance(
                *,
                bufsize:        int                            = __io_bufsize__,
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

    def __ior__(self, content: Union['Content', bytes], /) -> 'Content':
        if isinstance(content, Content):
            if abspath(content.__path__) == abspath(self.__path__):
                raise ge.IsSameFileError(
                    'source and destination cannot be the same, '
                    f'path "{abspath(self.__path__)}".'
                )
            read, write = content.rb().read, self.wb().write
            while True:
                content = read(__read_bufsize__)
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

    def __iadd__(self, content: Union['Content', bytes], /) -> 'Content':
        if isinstance(content, Content):
            read, write = content.rb().read, self.ab().write
            while True:
                content = read(__read_bufsize__)
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

    def __eq__(self, content: Union['Content', bytes], /) -> bool:
        if isinstance(content, Content):
            read1, read2 = self.rb().read, content.rb().read
            while True:
                content1 = read1(__read_bufsize__)
                content2 = read2(__read_bufsize__)
                if content1 == content2 == b'':
                    return True
                if content1 != content2:
                    return False
        elif content.__class__ is bytes:
            start, end = 0, __read_bufsize__
            read1 = self.rb().read
            while True:
                content1 = read1(__read_bufsize__)
                if content1 == content[start:end] == b'':
                    return True
                if content1 != content[start:end]:
                    return False
                start += __read_bufsize__
                end   += __read_bufsize__
        else:
            raise TypeError(
                'content type to be equality judgment operation can only be '
                f'"{__package__}.{Content.__name__}" or "bytes", '
                f'not "{content.__class__.__name__}".'
            )

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

    def append(self, content: Union['Content', bytes], /) -> None:
        self.__iadd__(content)

    def copy(
            self,
            other:   Union['Content', FileIO],
            /, *,
            bufsize: int                      = __read_bufsize__
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
        m5 = md5(salting)
        read = self.rb().read

        while True:
            content = read(__read_bufsize__)
            if not content:
                break
            m5.update(content)

        return m5.hexdigest()


def tree(
        dirpath:    Optional[PathLink] = None,
        /, *,
        level:      int                = None,
        bottom_up:  bool               = False,
        omit_dir:   bool               = False,
        mysophobia: bool               = False,
        shortpath:  bool               = False
) -> Generator:
    if dirpath == b'':
        dirpath: bytes = getcwdb()
    elif dirpath in (None, ''):
        dirpath: str = getcwd()

    return __tree__(
        dirpath,
        level     =level or sys.getrecursionlimit(),
        bottom_up =bottom_up,
        omit_dir  =omit_dir,
        root      =dirpath,
        nullchar  =b'' if dirpath.__class__ is bytes else '',
        mysophobia=mysophobia,
        shortpath =shortpath
    )


def __tree__(
        dirpath:    PathLink,
        /, *,
        level:      int,
        bottom_up:  bool,
        omit_dir:   bool,
        mysophobia: bool,
        shortpath:  bool,
        root:       PathLink,
        nullchar:   BytesOrStr
) -> Generator:
    for name in listdir(dirpath):
        path: PathLink = join(dirpath, name)
        is_dir: bool = isdir(path)

        if bottom_up:
            if level > 1 and is_dir:
                yield from __tree__(
                    path,
                    level     =level - 1,
                    bottom_up =bottom_up,
                    omit_dir  =omit_dir,
                    mysophobia=mysophobia,
                    shortpath =shortpath,
                    root      =root,
                    nullchar  =nullchar
                )
            if not is_dir or not omit_dir:
                if mysophobia:
                    if shortpath:
                        path: PathLink = path.replace(root, nullchar)
                        if path[0] in (47, 92, '/', '\\'):
                            path: PathLink = path[1:]
                    yield path
                else:
                    yield Directory(path) if is_dir else \
                        File(path) if isfile(path) else Path(path)
        else:
            if not is_dir or not omit_dir:
                if mysophobia:
                    if not shortpath:
                        yield path
                    else:
                        shortpath: PathLink = path.replace(root, nullchar)
                        if shortpath[0] in (47, 92, '/', '\\'):
                            shortpath: PathLink = shortpath[1:]
                        yield shortpath
                else:
                    yield Directory(path) if is_dir else \
                        File(path) if isfile(path) else Path(path)
            if level > 1 and is_dir:
                yield from __tree__(
                    path,
                    level     =level - 1,
                    bottom_up =bottom_up,
                    omit_dir  =omit_dir,
                    mysophobia=mysophobia,
                    shortpath =shortpath,
                    root      =root,
                    nullchar  =nullchar
                )


class SystemPath(Directory, File):
    __new__ = Directory.__new__

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

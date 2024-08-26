"""A Professional Library for File and System Path Manipulation

The `systempath` is a highly specialized library designed for Python developers
forfile and system path manipulation. By providing an intuitive and powerful
object-oriented API, it significantly simplifies complex file and directory
management tasks, allowing developers to focus more on implementing core
business logic rather than the intricacies of low-level file system operations.

    >>> from systempath import SystemPath, Directory, File

    >>> root = SystemPath('/')

    >>> home: Directory = root['home']['gqylpy']
    >>> home
    /home/gqylpy

    >>> file: File = home['alpha.txt']
    >>> file
    /home/gqylpy/alpha.txt

    >>> file.content
    b'GQYLPY \xe6\x94\xb9\xe5\x8f\x98\xe4\xb8\x96\xe7\x95\x8c'

────────────────────────────────────────────────────────────────────────────────
Copyright (c) 2022-2024 GQYLPY <http://gqylpy.com>. All rights reserved.

    @version: 1.2
    @author: 竹永康 <gqylpy@outlook.com>
    @source: https://github.com/gqylpy/systempath

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
import typing

from typing import (
    Type, TypeVar, Literal, Optional, Union, Dict, Tuple, List, Mapping,
    BinaryIO, TextIO, Callable, Sequence, Iterator, Iterable, Any
)

if typing.TYPE_CHECKING:
    import csv
    import json
    import yaml
    from _typeshed import SupportsWrite
    from configparser import ConfigParser, Interpolation

if sys.version_info >= (3, 10):
    from typing import TypeAlias
else:
    TypeAlias = TypeVar('TypeAlias')

if sys.version_info >= (3, 11):
    from typing import Self
else:
    Self = TypeVar('Self')

__all__ = ['SystemPath', 'Path', 'Directory', 'File', 'Open', 'Content', 'tree']

BytesOrStr:     TypeAlias = TypeVar('BytesOrStr', bytes, str)
PathLink:       TypeAlias = BytesOrStr
PathType:       TypeAlias = Union['Path', 'Directory', 'File', 'SystemPath']
FileOpener:     TypeAlias = Callable[[PathLink, int], int]
FileNewline:    TypeAlias = Literal['', '\n', '\r', '\r\n']
CopyFunction:   TypeAlias = Callable[[PathLink, PathLink], None]
CopyTreeIgnore: TypeAlias = \
    Callable[[PathLink, List[BytesOrStr]], List[BytesOrStr]]

ConvertersMap:       TypeAlias = Dict[str, Callable[[str], Any]]
CSVDialectLike:      TypeAlias = Union[str, 'csv.Dialect', Type['csv.Dialect']]
JsonObjectHook:      TypeAlias = Callable[[Dict[Any, Any]], Any]
JsonObjectParse:     TypeAlias = Callable[[str], Any]
JsonObjectPairsHook: TypeAlias = Callable[[List[Tuple[Any, Any]]], Any]
YamlDumpStyle:       TypeAlias = Literal['|', '>', '|+', '>+']

YamlLoader: TypeAlias = Union[
    Type['yaml.BaseLoader'], Type['yaml.Loader'], Type['yaml.FullLoader'],
    Type['yaml.SafeLoader'], Type['yaml.UnsafeLoader']
]
YamlDumper: TypeAlias = Union[
    Type['yaml.BaseDumper'], Type['yaml.Dumper'], Type['yaml.SafeDumper']
]

try:
    import exceptionx as ex
except ModuleNotFoundError:
    if os.path.basename(sys.argv[0]) != 'setup.py':
        raise
else:
    SystemPathNotFoundError:  Type[ex.Error] = ex.SystemPathNotFoundError
    NotAPathError:            Type[ex.Error] = ex.NotAPathError
    NotAFileError:            Type[ex.Error] = ex.NotAFileError
    NotADirectoryOrFileError: Type[ex.Error] = ex.NotADirectoryOrFileError
    IsSameFileError:          Type[ex.Error] = ex.IsSameFileError


class CSVReader(Iterator[List[str]]):
    line_num: int
    @property
    def dialect(self) -> 'csv.Dialect': ...
    def __next__(self) -> List[str]: ...


class CSVWriter:
    @property
    def dialect(self) -> 'csv.Dialect': ...
    def writerow(self, row: Iterable[Any]) -> Any: ...
    def writerows(self, rows: Iterable[Iterable[Any]]) -> None: ...


class Path:

    def __init__(
            self,
            name:            PathLink,
            /, *,
            autoabs:         Optional[bool] = None,
            strict:          Optional[bool] = None,
            dir_fd:          Optional[int]  = None,
            follow_symlinks: Optional[bool] = None
    ):
        """
        @param name
            A path link, hopefully absolute. If it is a relative path, the
            current working directory is used as the parent directory (the
            return value of `os.getcwd()`).

        @param autoabs
            Automatically normalize the path link and convert to absolute path,
            at initialization. The default is False. It is always recommended
            that you enable the parameter when the passed path is a relative
            path.

        @param strict
            Set to True to enable strict mode, which means that the passed path
            must exist, otherwise raise `SystemPathNotFoundError` (or other).
            The default is False.

        @param dir_fd
            This optional parameter applies only to the following methods:
                `readable`,    `writeable`, `executable`, `rename`,
                `renames`,     `replace`,   `symlink`,    `readlink`,
                `stat`,        `lstat`,     `chmod`,      `access`,
                `chown`,       `copy`,      `copystat`,   `copymode`,
                `lchmod`,      `chflags`,   `getxattr`,   `listxattr`,
                `removexattr`, `link`,      `unlink`,     `mknod`,
                `copy`

            A file descriptor open to a directory, obtain by `os.open`, sample
            `os.open('dir/', os.O_RDONLY)`. If this parameter is specified and
            the parameter `path` is relative, the parameter `path` will then be
            relative to that directory; otherwise, this parameter is ignored.

            This parameter may not be available on your platform, using them
            will ignore or raise `NotImplementedError` if unavailable.

        @param follow_symlinks
            This optional parameter applies only to the following methods:
                `readable`,  `writeable`,   `executable`, `copystat`,
                `copymode`,  `stat`,        `chmod`,      `access`,
                `chown`,     `chflags`,     `getxattr`,   `setxattr`,
                `listxattr`, `removexattr`, `walk`,       `copy`,
                `link`

            Used to indicate whether symbolic links are followed, the default is
            True. If specified as False, and the last element of the parameter
            `path` is a symbolic link, the action will point to the symbolic
            link itself, not to the path to which the link points.

            This parameter may not be available on your platform, using them
            will raise `NotImplementedError` if unavailable.
        """
        if strict and not os.path.exists(name):
            raise SystemPathNotFoundError

        self.name            = os.path.abspath(name) if autoabs else name
        self.strict          = strict
        self.dir_fd          = dir_fd
        self.follow_symlinks = follow_symlinks

    def __bytes__(self) -> bytes:
        """Return the path of type bytes."""

    def __eq__(self, other: [PathType, PathLink], /) -> bool:
        """Return True if the absolute path of the path instance is equal to the
        absolute path of another path instance (can also be a path link
        character) else False."""

    def __len__(self) -> int:
        """Return the length of the path string (or bytes)."""

    def __bool__(self) -> bool:
        return self.exists

    def __fspath__(self) -> PathLink:
        return self.name

    def __truediv__(self, subpath: Union[PathType, PathLink], /) -> PathType:
        """
        Concatenate paths, where the right path can be an instance of a path or
        a path link.Return a new concatenated path instance, whose
        characteristics are inherited from the left path.

        When `self.strict` is set to True, an exact instance of a directory or
        file is returned. Otherwise, an instance of `SystemPath` is generally
        returned.
        """

    def __add__(self, subpath: Union[PathType, PathLink], /) -> PathType:
        return self / subpath

    def __rtruediv__(self, dirpath: PathLink, /) -> PathType:
        """Concatenate paths, where the left path is a path link. Return a new
        concatenated path instance, whose characteristics are inherited from the
        right path."""

    def __radd__(self, dirpath: PathLink, /) -> PathType:
        return dirpath / self

    @property
    def basename(self) -> BytesOrStr:
        return os.path.basename(self)

    @property
    def dirname(self) -> 'Directory':
        return Directory(
            os.path.dirname(self),
            strict=self.strict,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def dirnamel(self, level: int) -> 'Directory':
        """Like `self.dirname`, and can specify the directory level."""
        return Directory(
            self.name.rsplit(os.sep, maxsplit=level)[0],
            strict=self.strict,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def ldirname(self, *, level: Optional[int] = None) -> PathType:
        """Cut the path from the left side, and can specify the cutting level
        through the parameter `level`, with a default of 1 level."""

    @property
    def abspath(self) -> PathType:
        return self.__class__(
            os.path.abspath(self),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def realpath(self, *, strict: Optional[bool] = None) -> PathType:
        return self.__class__(
            os.path.realpath(self, strict=strict),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def relpath(self, start: Optional[PathLink] = None) -> PathType:
        return self.__class__(
            os.path.relpath(self, start=start),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def normpath(self) -> PathType:
        return self.__class__(
            os.path.normpath(self),
            strict=self.strict,
            dir_fd=self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def expanduser(self) -> PathType:
        return self.__class__(
            os.path.expanduser(self),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def expandvars(self) -> PathType:
        return self.__class__(
            os.path.expandvars(self),
            strict=self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def split(self) -> Tuple[PathLink, BytesOrStr]:
        return os.path.split(self)

    def splitdrive(self) -> Tuple[BytesOrStr, PathLink]:
        return os.path.splitdrive(self)

    @property
    def isabs(self) -> bool:
        return os.path.isabs(self)

    @property
    def exists(self) -> bool:
        return os.path.exists(self)

    @property
    def lexists(self) -> bool:
        """Like `self.exists`, but do not follow symbolic links, return True for
        broken symbolic links."""
        return os.path.lexists(self)

    @property
    def isdir(self) -> bool:
        return os.path.isdir(self)

    @property
    def isfile(self) -> bool:
        return os.path.isfile(self)

    @property
    def islink(self) -> bool:
        return os.path.islink(self)

    @property
    def ismount(self) -> bool:
        return os.path.ismount(self)

    @property
    def is_block_device(self) -> bool:
        """Return True if the path is a block device else False."""

    @property
    def is_char_device(self) -> bool:
        """Return True if the path is a character device else False."""

    @property
    def isfifo(self) -> bool:
        """Return True if the path is a FIFO else False."""

    @property
    def isempty(self) -> bool:
        """Return True if the directory (or the contents of the file) is empty
        else False. If the `self.name` is not a directory or file then raise
        `NotADirectoryOrFileError`."""

    @property
    def readable(self) -> bool:
        return self.access(os.R_OK)

    @property
    def writeable(self) -> bool:
        return self.access(os.W_OK)

    @property
    def executable(self) -> bool:
        return self.access(os.X_OK)

    def delete(
            self,
            *,
            ignore_errors: Optional[bool] = None,
            onerror: Optional[Callable] = None
    ) -> None:
        """
        Delete the path, if the path is a file then call `os.remove` internally,
        if the path is a directory call `shutil.rmtree` internally.

        @param ignore_errors
            If the path does not exist will raise `FileNotFoundError`, can set
            this parameter to True to silence the exception. The default is
            False.

        @param onerror
            An optional error handler, used only if the path is a directory, for
            more instructions see `shutil.rmtree`.
        """

    def rename(self, dst: PathLink, /) -> PathLink:
        """
        Rename the file or directory, call `os.rename` internally.

        The optional initialization parameter `self.dir_fd` will be passed to
        parameters `src_dir_fd` and `dst_dir_fd` of `os.rename`.

        Important Notice:
        If the destination path is relative and is a single name, the parent
        path of the source is used as the parent path of the destination instead
        of using the current working directory, different from the traditional
        way.

        Backstory about providing this method
            https://github.com/gqylpy/systempath/issues/1

        @return: The destination path.
        """

    def renames(self, dst: PathLink, /) -> PathLink:
        """
        Rename the file or directory, super version of `self.rename`. Call
        `os.renames` internally.

        When renaming, the destination path is created if the destination path
        does not exist, including any intermediate directories; After renaming,
        the source path is deleted if it is empty, delete from front to back
        until the entire path is used or a nonempty directory is found.

        Important Notice:
        If the destination path is relative and is a single name, the parent
        path of the source is used as the parent path of the destination instead
        of using the current working directory, different from the traditional
        way.

        Backstory about providing this method
            https://github.com/gqylpy/systempath/issues/1

        @return: The destination path.
        """

    def replace(self, dst: PathLink, /) -> PathLink:
        """
        Rename the file or directory, overwrite if destination exists. Call
        `os.replace` internally.

        The optional initialization parameter `self.dir_fd` will be passed to
        parameters `src_dir_fd` and `dst_dir_fd` of `os.replace`.

        Important Notice:
        If the destination path is relative and is a single name, the parent
        path of the source is used as the parent path of the destination instead
        of using the current working directory, different from the traditional
        way.

        Backstory about providing this method
            https://github.com/gqylpy/systempath/issues/1

        @return: The destination path.
        """

    def move(
            self,
            dst: Union[PathType, PathLink],
            /, *,
            copy_function: Optional[Callable[[PathLink, PathLink], None]] = None
    ) -> Union[PathType, PathLink]:
        """
        Move the file or directory to another location, similar to the Unix
        system `mv` command. Call `shutil.move` internally.

        @param dst:
            Where to move, hopefully pass in an instance of `Path`, can also
            pass in a path link.

        @param copy_function
            The optional parameter `copy_function` will be passed directly to
            `shutil.move` and default value is `shutil.copy2`.

        Backstory about providing this method
            https://github.com/gqylpy/systempath/issues/1

        @return: The parameter `dst` is passed in, without any modification.
        """

    def copystat(
            self, dst: Union[PathType, PathLink], /
    ) -> Union[PathType, PathLink]:
        """
        Copy the metadata of the file or directory to another file or directory,
        call `shutil.copystat` internally.

        @param dst:
            Where to copy the metadata, hopefully pass in an instance of `Path`,
            can also pass in a path link.

        The copied metadata includes permission bits, last access time, and last
        modification time. On Unix, extended attributes are also copied where
        possible. The file contents, owner, and group are not copied.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, the action will point to the symbolic link itself,
        not to the path to which the link points, if and only if both the
        initialization parameter `self.name` and the parameter `dst` are
        symbolic links.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def copymode(
            self, dst: Union[PathType, PathLink], /
    ) -> Union[PathType, PathLink]:
        """
        Copy the mode bits of the file or directory to another file or
        directory, call `shutil.copymode` internally.

        @param dst:
            Where to copy the mode bits, hopefully pass in an instance of
            `Path`, can also pass in a path link.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, the action will point to the symbolic link itself,
        not to the path to which the link points, if and only if both the
        initialization parameter `self.name` and the parameter `dst` are
        symbolic links. But if `self.lchmod` isn't available (e.g. Linux) this
        method does nothing.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def symlink(
            self, dst: Union[PathType, PathLink], /
    ) -> Union[PathType, PathLink]:
        """
        Create a symbolic link to the file or directory, call `os.symlink`
        internally.

        @param dst:
            Where to create the symbolic link, hopefully pass in an instance of
            `Path`, can also pass in a path link.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def readlink(self) -> PathLink:
        """
        Return the path to which the symbolic link points.

        If the initialization parameter `self.name` is not a symbolic link, call
        this method will raise `OSError`.
        """

    @property
    def stat(self) -> os.stat_result:
        """
        Get the status of the file or directory, perform a stat system call
        against the file or directory. Call `os.stat` internally.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the path is a symbolic link,
        the action will point to the symbolic link itself, not to the path to
        which the link points.

        @return: os.stat_result(
            st_mode:  int   = access mode,
            st_ino:   int   = inode number,
            st_dev:   int   = device number,
            st_nlink: int   = number of hard links,
            st_uid:   int   = user ID of owner,
            st_gid:   int   = group ID of owner,
            st_size:  int   = total size in bytes,
            st_atime: float = time of last access,
            st_mtime: float = time of last modification,
            st_ctime: float = time of last change (on Unix) or created (on
                              Windows)
            ...
            More attributes, you can look up `os.stat_result`.
        )
        """

    @property
    def lstat(self) -> os.stat_result:
        """Get the status of the file or directory, like `self.stat`, but do not
        follow symbolic links."""
        return self.__class__(
            self.name, dir_fd=self.dir_fd, follow_symlinks=False
        ).stat

    def getsize(self) -> int:
        """Get the size of the file, return 0 if the path is a directory."""
        return os.path.getsize(self)

    def getctime(self) -> float:
        return os.path.getctime(self)

    def getmtime(self) -> float:
        return os.path.getmtime(self)

    def getatime(self) -> float:
        return os.path.getatime(self)

    def chmod(self, mode: int, /) -> None:
        """
        Change the access permissions of the file or directory, call `os.chmod`
        internally.

        @param mode
            Specify the access permissions, can be a permission mask (0o600),
            can be a combination (0o600|stat.S_IFREG), can be a bitwise (33152).

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the path is a symbolic link,
        the action will point to the symbolic link itself, not to the path to
        which the link points.
        """

    def access(
            self, mode: int, /, *, effective_ids: Optional[bool] = None
    ) -> bool:
        """
        Test access permissions to the path using the real uid/gid, call
        `os.access` internally.

        @param mode
            Test which access permissions, can be the inclusive-or(`|`) of:
                `os.R_OK`: real value is 4, whether readable.
                `os.W_OK`: real value is 2, whether writeable.
                `os.X_OK`: real value is 1, whether executable.
                `os.F_OK`: real value is 0, whether exists.

        @param effective_ids
            The default is False, this parameter may not be available on your
            platform, using them will ignore if unavailable. You can look up
            `os.access` for more description.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the path is a symbolic link,
        the action will point to the symbolic link itself, not to the path to
        which the link points.
        """

    if sys.platform != 'win32':
        def lchmod(self, mode: int, /) -> None:
            """Change the access permissions of the file or directory, like
            `self.chmod`, but do not follow symbolic links."""
            self.__class__(self.name, follow_symlinks=False).chmod(mode)

        @property
        def owner(self) -> str:
            """Get the login name of the path owner."""

        @property
        def group(self) -> str:
            """Get the group name of the path owner group."""

        def chown(self, uid: int, gid: int) -> None:
            """
            Change the owner and owner group of the file or directory, call
            `os.chown` internally.

            @param uid
                Specify the owner id, obtain by `os.getuid()`.

            @param gid
                Specify the owner group id, obtain by `os.getgid()`.

            If the optional initialization parameter `self.follow_symlinks` is
            specified as False, and the last element of the path is a symbolic
            link, the action will point to the symbolic link itself, not to the
            path to which the link points.
            """

        def lchown(self, uid: int, gid: int) -> None:
            """Change the owner and owner group of the file or directory, like
            `self.chown`, but do not follow symbolic links."""
            self.__class__(self.name, follow_symlinks=False).chown(uid, gid)

        def chflags(self, flags: int) -> None:
            """"
            Set the flag for the file or directory, different flag have
            different attributes. Call `os.chflags` internally.

            @param flags
                Specify numeric flag, can be the inclusive-or(`|`) of:
                    `stat.UF_NODUMP`:
                        do not dump file
                        real value is 0x00000001 (1)
                    `stat.UF_IMMUTABLE`:
                        file may not be changed
                        real value is 0x00000002 (2)
                    `stat.UF_APPEND`:
                        file may only be appended to
                        real value is 0x00000004 (4)
                    `stat.UF_OPAQUE`:
                        directory is opaque when viewed through a union stack
                        real value is 0x00000008 (8)
                    `stat.UF_NOUNLINK`:
                        file may not be renamed or deleted
                        real value is 0x00000010 (16)
                    `stat.UF_COMPRESSED`:
                        OS X: file is hfs-compressed
                        real value is 0x00000020 (32)
                    `stat.UF_HIDDEN`:
                        OS X: file should not be displayed
                        real value is 0x00008000 (32768)
                    `stat.SF_ARCHIVED`:
                        file may be archived
                        real value is 0x00010000 (65536)
                    `stat.SF_IMMUTABLE`:
                        file may not be changed
                        real value is 0x00020000 (131072)
                    `stat.SF_APPEND`:
                        file may only be appended to
                        real value is 0x00040000 (262144)
                    `stat.SF_NOUNLINK`:
                        file may not be renamed or deleted
                        real value is 0x00100000 (1048576)
                    `stat.SF_SNAPSHOT`:
                        file is a snapshot file
                        real value is 0x00200000 (2097152)

            If the optional initialization parameter `self.follow_symlinks` is
            specified as False, and the last element of the path is a symbolic
            link, the action will point to the symbolic link itself, not to the
            path to which the link points.

            Warning, do not attempt to set flags for important files and
            directories in your system, this may cause your system failure,
            unable to start!

            This method may not be available on your platform, using them will
            raise `NotImplementedError` if unavailable.
            """

        def lchflags(self, flags: int) -> None:
            """Set the flag for the file or directory, like `self.chflags`, but
            do not follow symbolic links."""
            self.__class__(self.name, follow_symlinks=False).chflags(flags)

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            """
            Change the hidden attributes of the file or directory, call the Unix
            system command `chattr` internally.

            @param operator
                Specify an operator "+", "-", or "=". Used with the parameter
                `attributes` to add, remove, or reset certain attributes.

            @param attrs
                a: Only data can be appended.
                A: Tell the system not to change the last access time to the
                   file or directory. However, this attribute is automatically
                   removed after manual modification.
                c: Compress the file or directory and save it.
                d: Exclude the file or directory from the "dump" operation, the
                   file or directory is not backed up by "dump" when the "dump"
                   program is executed.
                e: Default attribute, this attribute indicates that the file or
                   directory is using an extended partition to map blocks on
                   disk.
                D: Check for errors in the compressed file.
                i: The file or directory is not allowed to be modified.
                u: Prevention of accidental deletion, when the file or directory
                   is deleted, the system retains the data block so that it can
                   recover later.
                s: As opposed to the attribute "u", when deleting the file or
                   directory, it will be completely deleted (fill the disk
                   partition with 0) and cannot be restored.
                S: Update the file or directory instantly.
                t: The tail-merging, file system support tail merging.
                ...
                More attributes that are rarely used (or no longer used), you
                can refer to the manual of the Unix system command `chattr`.

            Use Warning, the implementation of method `chattr` is to directly
            call the system command `chattr`, so this is very unreliable. Also,
            do not attempt to modify hidden attributes of important files and
            directories in your system, this may cause your system failure,
            unable to start!
            """

        def lsattr(self) -> str:
            """
            Get the hidden attributes of the file or directory, call the Unix
            system command `lsattr` internally.

            Use Warning, the implementation of method `lsattr` is to directly
            call the system command `lsattr`, so this is very unreliable.
            """

        def exattr(self, attr: str, /) -> bool:
            """
            Check whether the file or directory has the hidden attribute and
            return True or False.

            The usage of parameter `attr` can be seen in method `self.chattr`.
            """
            return attr in self.lsattr()

        if sys.platform == 'linux':
            def getxattr(self, attribute: BytesOrStr, /) -> bytes:
                """Return the value of extended attribute on path, you can look
                up `os.getxattr` for more description."""

            def setxattr(
                    self,
                    attribute: BytesOrStr,
                    value: bytes,
                    *,
                    flags: Optional[int] = None
            ) -> None:
                """
                Set extended attribute on path to value, you can look up
                `os.setxattr` for more description.

                If the optional initialization parameter `self.follow_symlinks`
                is specified as False, and the last element of the path is a
                symbolic link, the action will point to the symbolic link
                itself, not to the path to which the link points.
                """

            def listxattr(self) -> List[str]:
                """
                Return a list of extended attributes on path, you can look up
                `os.listxattr` for more description.

                If the optional initialization parameter `self.follow_symlinks`
                is specified as False, and the last element of the path is a
                symbolic link, the action will point to the symbolic link
                itself, not to the path to which the link points.
                """

            def removexattr(self, attribute: BytesOrStr, /) -> None:
                """
                Remove extended attribute on path, you can look up
                `os.removexattr` for more description.

                If the optional initialization parameter `self.follow_symlinks`
                is specified as False, and the last element of the path is a
                symbolic link, the action will point to the symbolic link
                itself, not to the path to which the link points.
                """

    def utime(
            self,
            /,
            times: Optional[Tuple[Union[float, int], Union[float, int]]] = None
    ) -> None:
        """
        Set the access and modified time of the file or directory, call
        `os.utime` internally.

        @param times
            Pass in a tuple (atime, mtime) to specify access time and modify
            time respectively. If not specified then use current time.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the path is a symbolic link,
        the action will point to the symbolic link itself, not to the path to
        which the link points.
        """


class Directory(Path):
    """Pass a directory path link to get a directory object, which you can then
    use to do anything a directory can do."""

    def __getitem__(self, name: BytesOrStr) -> PathType:
        path: PathLink = os.path.join(self, name)

        if self.strict:
            if os.path.isdir(path):
                return Directory(path, strict=self.strict)
            if os.path.isfile(path):
                return File(path)
            if os.path.exists(name):
                return Path(name)
            raise SystemPathNotFoundError

        return SystemPath(path)

    def __delitem__(self, name: BytesOrStr) -> None:
        Path(os.path.join(self, name)).delete()

    def __iter__(self) -> Iterator[Union['Directory', 'File', Path]]:
        return self.subpaths

    def __bool__(self) -> bool:
        return self.isdir

    @staticmethod
    def home(
            *,
            strict: Optional[bool] = None,
            follow_symlinks: Optional[bool] = None
    ) -> 'Directory':
        return Directory(
            '~', strict=strict, follow_symlinks=follow_symlinks
        ).expanduser()

    @property
    def subpaths(self) -> Iterator[Union['Directory', 'File', Path]]:
        """Get the instances of `Directory` or `File` for all subpaths (single
        layer) in the directory."""

    @property
    def subpath_names(self) -> List[BytesOrStr]:
        """Get the names of all subpaths (single layer) in the directory. Call
        `os.listdir` internally."""

    def scandir(self) -> Iterator[os.DirEntry]:
        """Get instances of `os.DirEntry` for all files and subdirectories
        (single layer) in the directory, call `os.scandir` internally."""

    def tree(
            self,
            *,
            level:     Optional[int]  = None,
            downtop:   Optional[bool] = None,
            omit_dir:  Optional[bool] = None,
            pure_path: Optional[bool] = None,
            shortpath: Optional[bool] = None
    ) -> Iterator[Union[Path, PathLink]]:
        return tree(
            self.name,
            level    =level,
            downtop  =downtop,
            omit_dir =omit_dir,
            pure_path=pure_path,
            shortpath=shortpath
        )

    def walk(
            self,
            *,
            topdown: Optional[bool] = None,
            onerror: Optional[Callable] = None
    ) -> Iterator[Tuple[PathLink, List[BytesOrStr], List[BytesOrStr]]]:
        """
        Directory tree generator, recurse the directory to get all
        subdirectories and files, yield a 3-tuple for each subdirectory, call
        `os.walk` internally.

        The yielding 3-tuple is as follows:
            (current_directory_path, all_subdirectory_names, all_file_names)

        @param topdown
            The default is True, generate the directory tree from the outside
            in. If specified as False, from the inside out.

        @param onerror
            An optional error handler, for more instructions see `os.walk`.
        """

    def search(
            self,
            slicing:   BytesOrStr,
            /, *,
            level:     Optional[int]  = None,
            omit_dir:  Optional[bool] = None,
            pure_path: Optional[bool] = None,
            shortpath: Optional[bool] = None
    ) -> Iterator[Union[PathType, PathLink]]:
        """
        Search for all paths containing the specified string fragment in the
        current directory (and its subdirectories, according to the specified
        search depth). It traverses the directory tree, checking whether each
        path (which can be the path of a file or subdirectory) contains the
        specified slicing string `slicing`. If a matching path is found, it
        produces these paths as results.

        @param slicing
            The path slicing, which can be any part of the path.

        @param level
            Recursion depth of the directory, default is deepest. An int must be
            passed in, any integer less than 1 is considered to be 1, warning
            passing decimals can cause depth confusion.

        @param omit_dir
            Omit all subdirectories when yielding paths. The default is False.

        @param pure_path
            By default, if the subpath is a directory then yield a `Directory`
            object, if the subpath is a file then yield a `File` object. If set
            this parameter to True, directly yield the path link string (or
            bytes). This parameter is not recommended for use.

        @param shortpath
            Yield short path link string, delete the `dirpath` from the left end
            of the path, used with the parameter `pure_path`. The default is
            False.
        """

    def copytree(
            self,
            dst:                      Union['Directory', PathLink],
            /, *,
            symlinks:                 Optional[bool]               = None,
            ignore:                   Optional[CopyTreeIgnore]     = None,
            copy_function:            Optional[CopyFunction]       = None,
            ignore_dangling_symlinks: Optional[bool]               = None,
            dirs_exist_ok:            Optional[bool]               = None
    ) -> Union['Directory', PathLink]:
        """
        Copy the directory tree recursively, call `shutil.copytree` internally.

        @param dst
            Where to copy the directory, hopefully pass in an instance of
            `Directory`, can also pass in a file path link.

        @param symlinks
            For symbolic links in the source tree, the content of the file to
            which the symbolic link points is copied by default. If this
            parameter is set to True, the symbolic link itself is copied.
            The default is False.

            If the file to which the symbolic link points does not exist, raise
            an exception at the end of the replication process. If you do not
            want this exception raised, set the parameter
            `ignore_dangling_symlinks` to True.

        @param ignore
            An optional callable parameter, used to manipulate the directory
            `copytree` is accessing, and return a list of content names relative
            to those that should not be copied. Can like this:

                >>> def func(
                >>>         src: PathLink, names: List[BytesOrStr]
                >>> ) -> List[BytesOrStr]:
                >>>     '''
                >>>     @param src
                >>>         The directory that `copytree` is accessing.
                >>>     @param names
                >>>         A list of the content names of the directories being
                >>>         accessed.
                >>>     @return
                >>>         A list of content names relative  to those that
                >>>         should not be copied
                >>>     '''
                >>>     return [b'alpha.txt', b'beta.txt']

            For more instructions see `shutil.copytree`.

        @param copy_function
            The optional parameter `copy_function` will be passed directly to
            `shutil.copytree` and default value is `shutil.copy2`.

        @param ignore_dangling_symlinks
            Used to ignore exceptions raised by symbolic link errors, use with
            parameter `symlinks`. The default is False. This parameter has no
            effect on platforms that do not support `os.symlink`.

        @param dirs_exist_ok
            If the destination path already exists will raise `FileExistsError`,
            can set this parameter to True to silence the exception and
            overwrite the files in the target. Default is False.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def clear(self) -> None:
        """
        Clear the directory.

        Traverse everything in the directory and delete it, call `self.rmtree`
        for the directories and `File.remove` for the files (or anything else).
        """

    def mkdir(
            self,
            mode: Optional[int] = None,
            *,
            ignore_exists: Optional[bool] = None
    ) -> None:
        """
        Create the directory on your system, call `os.mkdir` internally.

        @param mode
            Specify the access permissions for the directory, can be a
            permission mask (0o600), can be a combination (0o600|stat.S_IFREG),
            can be a bitwise (33152). Default is 0o777.

            This parameter is ignored if your platform is Windows.

        @param ignore_exists
            If the directory already exists, call this method will raise
            `FileExistsError`. But, if this parameter is set to True then
            silently skip. The default is False.
        """

    def makedirs(
            self,
            mode: Optional[int] = None,
            *,
            exist_ok: Optional[bool] = None
    ) -> None:
        """
        Create the directory and all intermediate ones, super version of
        `self.mkdir`. Call `os.makedirs` internally.

        @param mode
            Specify the access permissions for the directory, can be a
            permission mask (0o600), can be a combination (0o600|stat.S_IFREG),
            can be a bitwise (33152). Default is 0o777.

            This parameter is ignored if your platform is Windows.

        @param exist_ok
            If the directory already exists will raise `FileExistsError`, can
            set this parameter to True to silence the exception. The default is
            False.
        """

    def rmdir(self) -> None:
        """Delete the directory on your system, if the directory is not empty
        then raise `OSError`. Call `os.rmdir` internally."""

    def removedirs(self) -> None:
        """
        Delete the directory and all empty intermediate ones, super version of
        `self.rmdir`. Call `os.removedirs` internally.

        Delete from the far right, terminates until the whole path is consumed
        or a non-empty directory is found. if the leaf directory is not empty
        then raise `OSError`.
        """

    def rmtree(
            self,
            *,
            ignore_errors: Optional[bool] = None,
            onerror: Optional[Callable] = None
    ) -> None:
        """
        Delete the directory tree recursively, call `shutil.rmtree` internally.

        @param ignore_errors
            If the directory does not exist will raise `FileNotFoundError`, can
            set this parameter to True to silence the exception. The default is
            False.

        @param onerror
            An optional error handler, described more see `shutil.rmtree`.
        """

    def chdir(self) -> None:
        """Change the working directory of the current process to the directory.
        """
        os.chdir(self)


class File(Path):
    """Pass a file path link to get a file object, which you can then use to do
    anything a file can do."""

    def __bool__(self) -> bool:
        return self.isfile

    def __contains__(self, subcontent: bytes, /) -> bool:
        return subcontent in self.contents

    def __iter__(self) -> Iterator[bytes]:
        yield from self.contents

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

    content = property(
        lambda self         : self.contents.read(),
        lambda self, content: self.contents.overwrite(content),
        lambda self         : self.contents.clear(),
        """Quickly read, rewrite, or empty all contents of the file (in binary
        mode). Note that for other operations on the file contents, use
        `contents`."""
    )

    @property
    def contents(self) -> 'Content':
        """Operation the file content, super version of `self.content`."""
        return Content(self)

    @contents.setter
    def contents(self, content: ['Content', bytes]) -> None:
        """Do nothing, syntax hints for compatibility with `Content.__iadd__`
        and `Content.__ior__` only."""

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return os.path.splitext(self)

    @property
    def extension(self) -> BytesOrStr:
        return os.path.splitext(self)[1]

    def copy(self, dst: Union['File', PathLink], /) -> Union['File', PathLink]:
        """
        Copy the file to another location, call `shutil.copyfile` internally.

        @param dst:
            Where to copy the file, hopefully pass in an instance of `File`, can
            also pass in a file path link.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the file path is a symbolic
        link, will create a new symbolic link instead of copy the file to which
        the link points to.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def copycontent(
            self,
            dst: Union['File', 'SupportsWrite[bytes]'],
            /, *,
            bufsize: Optional[int] = None
    ) -> Union['File', 'SupportsWrite[bytes]']:
        """
        Copy the file contents to another file.

        @param dst
            Where to copy the file contents, hopefully pass in an instance of
            `File`. Can also pass in a stream of the destination file (or called
            handle), it must have at least writable or append permission.

        @param bufsize
            The buffer size, the length of each copy, default is 64K (if your
            platform is Windows then 1M). Passing -1 turns off buffering.

        @return: The parameter `dst` is passed in, without any modification.
        """
        warnings.warn(
            f'will be deprecated soon, replaced to {self.contents.copy}.',
            DeprecationWarning
        )

    def link(self, dst: Union['File', PathLink], /) -> Union['File', PathLink]:
        """
        Create a hard link to the file, call `os.link` internally.

        @param dst:
            Where to create the hard link for the file, hopefully pass in an
            instance of `File`, can also pass in a file path link.

        The optional initialization parameter `self.dir_fd` will be passed to
        parameters `src_dir_fd` and `dst_dir_fd` of `os.link`.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the file path is a symbolic
        link, will create a link to the symbolic link itself instead of the file
        to which the link points to.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def mknod(
            self,
            mode: Optional[int] = None,
            *,
            device: Optional[int] = None,
            ignore_exists: Optional[bool] = None
    ) -> None:
        """
        Create the file, call `os.mknod` internally, but if your platform is
        Windows then internally call `open(self.name, 'x')`.

        @param mode
            Specify the access permissions of the file, can be a permission
            mask (0o600), can be a combination (0o600|stat.S_IFREG), can be a
            bitwise (33152), and default is 0o600(-rw-------).

        @param device
            Default 0, this parameter may not be available on your platform,
            using them will ignore if unavailable. You can look up `os.mknod`
            for more description.

        @param ignore_exists
            If the file already exists, call this method will raise
            `FileExistsError`. But, if this parameter is set to True then
            silently skip. The default is False.
        """

    def mknods(
            self,
            mode: Optional[int] = None,
            *,
            device: Optional[int] = None,
            ignore_exists: Optional[bool] = None
    ) -> None:
        """Create the file and all intermediate paths, super version of
        `self.mknod`."""
        self.dirname.makedirs(mode, exist_ok=True)
        self.mknod(mode, device=device, ignore_exists=ignore_exists)

    def create(
            self,
            mode: Optional[int] = None,
            *,
            device: Optional[int] = None,
            ignore_exists: Optional[bool] = None
    ):
        warnings.warn(
            f'will be deprecated soon, replaced to {self.mknod}.',
            DeprecationWarning
        )
        self.mknod(mode, device=device, ignore_exists=ignore_exists)

    def creates(
            self,
            mode: Optional[int] = None,
            *,
            device: Optional[int] = None,
            ignore_exists: Optional[bool] = None
    ) -> None:
        warnings.warn(
            f'will be deprecated soon, replaced to {self.mknods}.',
            DeprecationWarning
        )
        self.mknods(mode, device=device, ignore_exists=ignore_exists)

    def remove(self, *, ignore_errors: Optional[bool] = None) -> None:
        """
        Remove the file, call `os.remove` internally.

        @param ignore_errors
            If the file does not exist will raise `FileNotFoundError`, can set
            this parameter to True to silence the exception. The default is
            False.
        """

    def unlink(self) -> None:
        """Remove the file, like `self.remove`, call `os.unlink` internally."""

    def contains(self, subcontent: bytes, /) -> bool:
        return self.contents.contains(subcontent)

    def truncate(self, length: int) -> None:
        self.contents.truncate(length)

    def clear(self) -> None:
        self.contents.clear()

    def md5(self, salting: Optional[bytes] = None) -> str:
        return self.contents.md5(salting)

    def read(
            self,
            size: Optional[int] = None,
            /, *,
            encoding: Optional[str] = None
    ) -> str:
        warnings.warn(
            f'deprecated, replaced to {self.content} or {self.contents.read}.',
            DeprecationWarning
        )
        return self.open.r(encoding=encoding).read(size)

    def write(self, content: str, /, *, encoding: Optional[str] = None) -> int:
        warnings.warn(
            f'deprecated, replaced to {self.content} or {self.contents.write}.',
            DeprecationWarning
        )
        return self.open.w(encoding=encoding).write(content)

    def append(self, content: str, /, *, encoding: Optional[str] = None) -> int:
        warnings.warn(
            f'deprecated, replaced to {self.contents.append}.',
            DeprecationWarning
        )
        return self.open.a(encoding=encoding).write(content)


class Open:
    """
    Open a file and return a file stream (or called handle).

    >>> f: BinaryIO = Open('alpha.bin').rb()  # open for reading in binary mode.
    >>> f: TextIO   = Open('alpha.txt').r()   # open for reading in text mode.

    Pass in an instance of `File` (or a file path link) at instantiation time.
    At instantiation time (do nothing) the file will not be opened, only when
    you call one of the following methods, the file will be opened (call once,
    open once), open mode equals method name (where method `rb_plus` equals mode
    "rb+").

    ============================== IN BINARY MODE ==============================
    | Method  | Description                                                    |
    ----------------------------------------------------------------------------
    | rb      | open to read, if the file does not exist then raise            |
    |         | `FileNotFoundError`                                            |
    ----------------------------------------------------------------------------
    | wb      | open to write, truncate the file first, if the file does not   |
    |         | exist then create it                                           |
    ----------------------------------------------------------------------------
    | xb      | create a new file and open it to write, if the file already    |
    |         | exists then raise `FileExistsError`                            |
    ----------------------------------------------------------------------------
    | ab      | open to write, append to the end of the file, if the file does |
    |         | not exist then create it                                       |
    ----------------------------------------------------------------------------
    | rb_plus | open to read and write, if the file does not exist then raise  |
    |         | `FileNotFoundError`                                            |
    ----------------------------------------------------------------------------
    | wb_plus | open to write and read, truncate the file first, if the file   |
    |         | does not exist then create it                                  |
    ----------------------------------------------------------------------------
    | xb_plus | create a new file and open it to write and read, if the file   |
    |         | already exists then raise `FileExistsError`                    |
    ----------------------------------------------------------------------------
    | ab_plus | open to write and read, append to the end of the file, if the  |
    |         | file does not exist then create it                             |
    ----------------------------------------------------------------------------

    =============================== IN TEXT MODE ===============================
    | Method | Description                                                     |
    ----------------------------------------------------------------------------
    | r      | open to read, if the file does not exist then raise             |
    |        | `FileNotFoundError`                                             |
    ----------------------------------------------------------------------------
    | w      | open to write, truncate the file first, if the file does not    |
    |        | exist then create it                                            |
    ----------------------------------------------------------------------------
    | x      | create a new file and open it to write, if the file already     |
    |        | exists then raise `FileExistsError`                             |
    ----------------------------------------------------------------------------
    | a      | open to write, append to the end of the file, if the file does  |
    |        | not exist then create it                                        |
    ----------------------------------------------------------------------------
    | r_plus | open to read and write, if the file does not exist then raise   |
    |        | `FileNotFoundError`                                             |
    ----------------------------------------------------------------------------
    | w_plus | open to write and read, truncate the file first, if the file    |
    |        | does not exist then create it                                   |
    ----------------------------------------------------------------------------
    | x_plus | create a new file and open it to write and read, if the file    |
    |        | already exists then raise `FileExistsError`                     |
    ----------------------------------------------------------------------------
    | a_plus | open to write and read, append to the end of the file, if the   |
    |        | file does not exist then create it                              |
    ----------------------------------------------------------------------------

    @param bufsize
        Pass an integer greater than 0 to set the buffer size, 0 in bianry mode
        to turn off buffering, 1 in text mode to use line buffering. The buffer
        size is selected by default using a heuristic (reference
        `io.DEFAULT_BUFFER_SIZE`, on most OS, the buffer size is usually 8192 or
        4096 bytes), for "interactive" text files (files for which call
        `isatty()` returns True), line buffering is used by default.

    @param encoding
        The name of the encoding used to decode or encode the file (usually
        specified as "UTF-8"). The default encoding is platform-based and
        `locale.getpreferredencoding(False)` is called to get the current locale
        encoding. For the list of supported encodings, see the `codecs` module.

    @param errors
        Specify how to handle encoding errors (how strict encoding is), default
        is "strict" (maximum strictness, equivalent to passing None), if
        encoding error then raise `ValueError`. You can pass "ignore" to ignore
        encoding errors (caution ignoring encoding errors may result in data
        loss). The supported encoding error handling modes are as follows:

        --------------------------------------------------------------------
        | static            | raise `ValueError` (or its subclass)         |
        --------------------------------------------------------------------
        | ignore            | ignore the character, continue with the next |
        --------------------------------------------------------------------
        | replace           | replace with a suitable character            |
        --------------------------------------------------------------------
        | surrogateescape   | replace with private code points U+DCnn      |
        --------------------------------------------------------------------
        | xmlcharrefreplace | replace with a suitable XML character        |
        |                   | reference (only for encoding)                |
        --------------------------------------------------------------------
        | backslashreplace  | replace with backslash escape sequence       |
        --------------------------------------------------------------------
        | namereplace       | replace \\N{...} escape sequence (only for   |
        |                   | encoding)                                    |
        --------------------------------------------------------------------

        The allowed set of values can be extended via `codecs.register_error`,
        for more instructions see the `codecs.Codec` class.

    @param newline
        Specify how universal newline character works, can be None, "", "\n",
        "\r" and "\r\n". For more instructions see the `_io.TextIOWrapper`
        class.

    @param line_buffering
        If set to True, automatically call `flush()` when writing contains a
        newline character, The default is False.

    @param write_through
        We do not find any description of this parameter in the Python3 source
        code.

    @param opener
        You can customize the file opener by this parameter, custom file opener
        can like this:
            >>> def opener(file: str, flags: int) -> int:
            >>>     return os.open(file, os.O_RDONLY)
    """

    def __init__(self, file: Union[File, PathLink], /):
        self.file = file

    def rb(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def wb(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def xb(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def ab(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def rb_plus(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def wb_plus(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def xb_plus(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def ab_plus(
            self,
            *,
            bufsize: Optional[int]        = None,
            opener:  Optional[FileOpener] = None
    ) -> BinaryIO: ...

    def r(
            self,
            *,
            bufsize:  Optional[int]         = None,
            encoding: Optional[str]         = None,
            errors:   Optional[str]         = None,
            newline:  Optional[FileNewline] = None,
            opener:   Optional[FileOpener]  = None
    ) -> TextIO: ...

    def w(
            self,
            *,
            bufsize:        Optional[int]         = None,
            encoding:       Optional[str]         = None,
            errors:         Optional[str]         = None,
            newline:        Optional[FileNewline] = None,
            line_buffering: Optional[bool]        = None,
            write_through:  Optional[bool]        = None,
            opener:         Optional[FileOpener]  = None
    ) -> TextIO: ...

    def x(
            self,
            *,
            bufsize:        Optional[int]         = None,
            encoding:       Optional[str]         = None,
            errors:         Optional[str]         = None,
            newline:        Optional[FileNewline] = None,
            line_buffering: Optional[bool]        = None,
            write_through:  Optional[bool]        = None,
            opener:         Optional[FileOpener]  = None
    ) -> TextIO: ...

    def a(
            self,
            *,
            bufsize:        Optional[int]         = None,
            encoding:       Optional[str]         = None,
            errors:         Optional[str]         = None,
            newline:        Optional[FileNewline] = None,
            line_buffering: Optional[bool]        = None,
            write_through:  Optional[bool]        = None,
            opener:         Optional[FileOpener]  = None
    ) -> TextIO: ...

    def r_plus(
            self,
            *,
            bufsize:        Optional[int]         = None,
            encoding:       Optional[str]         = None,
            errors:         Optional[str]         = None,
            newline:        Optional[FileNewline] = None,
            line_buffering: Optional[bool]        = None,
            write_through:  Optional[bool]        = None,
            opener:         Optional[FileOpener]  = None
    ) -> TextIO: ...

    def w_plus(
            self,
            *,
            bufsize:        Optional[int]         = None,
            encoding:       Optional[str]         = None,
            errors:         Optional[str]         = None,
            newline:        Optional[FileNewline] = None,
            line_buffering: Optional[bool]        = None,
            write_through:  Optional[bool]        = None,
            opener:         Optional[FileOpener]  = None
    ) -> TextIO: ...

    def x_plus(
            self,
            *,
            bufsize:        Optional[int]         = None,
            encoding:       Optional[str]         = None,
            errors:         Optional[str]         = None,
            newline:        Optional[FileNewline] = None,
            line_buffering: Optional[bool]        = None,
            write_through:  Optional[bool]        = None,
            opener:         Optional[FileOpener]  = None
    ) -> TextIO: ...

    def a_plus(
            self,
            *,
            bufsize:        Optional[int]         = None,
            encoding:       Optional[str]         = None,
            errors:         Optional[str]         = None,
            newline:        Optional[FileNewline] = None,
            line_buffering: Optional[bool]        = None,
            write_through:  Optional[bool]        = None,
            opener:         Optional[FileOpener]  = None
    ) -> TextIO: ...


class Content:
    """Pass in an instance of `File` (or a file path link) to get a file content
    object, which you can then use to operation the contents of the file (in
    binary mode)."""

    def __init__(self, file: Union[File, PathLink], /):
        self.file = file

    def __bytes__(self) -> bytes:
        return self.read()

    def __ior__(self, other: Union['Content', bytes], /) -> Self:
        self.write(other)
        return self

    def __iadd__(self, other: Union['Content', bytes], /) -> Self:
        self.append(other)
        return self

    def __eq__(self, other: Union['Content', bytes], /) -> bool:
        """Whether the contents of the current file equal the contents of
        another file (or a bytes object). If they all point to the same file
        then direct return True."""

    def __contains__(self, subcontent: bytes, /) -> bool:
        return self.contains(subcontent)

    def __iter__(self) -> Iterator[bytes]:
        """Iterate over the file by line, omitting newline symbol and ignoring
        the last blank line."""

    def __len__(self) -> int:
        """Return the length (actually the size) of the file contents."""

    def __bool__(self) -> bool:
        """Return True if the file has content else False."""

    def read(self, size: Optional[int] = None, /) -> bytes:
        return Open(self.file).rb().read(size)

    def write(self, content: Union['Content', bytes], /) -> int:
        """Overwrite the current file content from another file content (or a
        bytes object)."""

    def overwrite(self, content: Union['Content', bytes], /) -> int:
        warnings.warn(
            f'will be deprecated soon, replaced to {self.write}.',
            DeprecationWarning
        )
        return self.write(content)

    def append(self, content: Union['Content', bytes], /) -> int:
        """Append the another file contents (or a bytes object) to the current
        file."""

    def contains(self, subcontent: bytes, /) -> bool:
        """Return True if the current file content contain `subcontent` else
        False."""

    def copy(
            self,
            dst: Union['Content', 'SupportsWrite[bytes]'] = None,
            /, *,
            bufsize: Optional[int] = None
    ) -> None:
        """
        Copy the file contents to another file.

        @param dst
            Where to copy the file contents, hopefully pass in an instance of
            `Content`. Can also pass in a stream of the destination file (or
            called handle), it must have at least writable or append permission.

        @param bufsize
            The buffer size, the length of each copy, default is 64K (if your
            platform is Windows then 1M). Passing -1 turns off buffering.
        """

    def truncate(self, length: int, /) -> None:
        """Truncate the file content to specific length."""

    def clear(self) -> None:
        self.truncate(0)

    def md5(self, salting: Optional[bytes] = None) -> str:
        """Return the md5 string of the file content."""


def tree(
        dirpath:   Optional[PathLink] = None,
        /, *,
        level:     Optional[int]      = None,
        downtop:   Optional[bool]     = None,
        omit_dir:  Optional[bool]     = None,
        pure_path: Optional[bool]     = None,
        shortpath: Optional[bool]     = None
) -> Iterator[Union[Path, PathLink]]:
    """
    Directory tree generator, recurse the directory to get all subdirectories
    and files.

    @param dirpath
        Specify a directory path link, recurse this directory on call to get all
        subdirectories and files, default is current working directory (the
        return value of `os.getcwd()`).

    @param level
        Recursion depth of the directory, default is deepest. An int must be
        passed in, any integer less than 1 is considered to be 1, warning
        passing decimals can cause depth confusion.

    @param downtop
        By default, the outer path is yielded first, from which the inner path
        is yielded. If your requirements are opposite, set this parameter to
        True.

    @param omit_dir
        Omit all subdirectories when yielding paths. The default is False.

    @param pure_path
        By default, if the subpath is a directory then yield a `Directory`
        object, if the subpath is a file then yield a `File` object. If set this
        parameter to True, directly yield the path link string (or bytes). This
        parameter is not recommended for use.

    @param shortpath
        Yield short path link string, delete the `dirpath` from the left end of
        the path, used with the parameter `pure_path`. The default is False.
    """


class INI:
    """
    Class to read and parse INI file.

    @param encoding
        The encoding used to read files is usually specified as "UTF-8". The
        default encoding is platform-based, and
        `locale.getpreferredencoding(False)` is called to obtain the current
        locale encoding. For a list of supported encodings, please refer to the
        `codecs` module.

    @param defaults
        A dictionary containing default key-value pairs to use if some options
        are missing in the parsed configuration file.

    @param dict_type
        The type used to represent the returned dictionary. The default is
        `dict`, which means that sections and options in the configuration will
        be preserved in the order they appear in the file.

    @param allow_no_value
        A boolean specifying whether options without values are allowed. If set
        to True, lines like `key=` will be accepted and the value of key will be
        set to None.

    @param delimiters
        A sequence of characters used to separate keys and values. The default
        is `("=", ":")`, which means both "=" and ":" can be used as delimiters.

    @param comment_prefixes
        A sequence of prefixes used to identify comment lines. The default is
        `("#", ";")`, which means lines starting with "#" or ";" will be
        considered comments.

    @param inline_comment_prefixes
        A sequence of prefixes used to identify inline comments. The default is
        None, which means inline comments are not supported.

    @param strict
        A boolean specifying whether to parse strictly. If set to True, the
        parser will report syntax errors, such as missing sections or incorrect
        delimiters.

    @param empty_lines_in_values
        A boolean specifying whether empty lines within values are allowed. If
        set to True, values can span multiple lines, and empty lines will be
        preserved.

    @param default_section
        The name of the default section in the configuration file is "DEFAULT"
        by default. If specified, any options that do not belong to any section
        during parsing will be added to this default section.

    @param interpolation
        Specifies the interpolation type. Interpolation is a substitution
        mechanism that allows values in the configuration file to reference
        other values. Supports `configparser.BasicInterpolation` and
        `configparser.ExtendedInterpolation`.

    @param converters
        A dictionary containing custom conversion functions used to convert
        string values from the configuration file to other types. The keys are
        the names of the conversion functions, and the values are the
        corresponding conversion functions.
    """

    def __init__(self, file: File, /):
        self.file = file

    def read(
            self,
            encoding:                Optional[str]                     = None,
            *,
            defaults:                Optional[Mapping[str, str]]       = None,
            dict_type:               Optional[Type[Mapping[str, str]]] = None,
            allow_no_value:          Optional[bool]                    = None,
            delimiters:              Optional[Sequence[str]]           = None,
            comment_prefixes:        Optional[Sequence[str]]           = None,
            inline_comment_prefixes: Optional[Sequence[str]]           = None,
            strict:                  Optional[bool]                    = None,
            empty_lines_in_values:   Optional[bool]                    = None,
            default_section:         Optional[str]                     = None,
            interpolation:           Optional['Interpolation']         = None,
            converters:              Optional[ConvertersMap]           = None
    ) -> 'ConfigParser': ...


class CSV:
    """
    A class to handle CSV file reading and writing operations.

    @param dialect:
        The dialect to use for the CSV file format. A dialect is a set of
        specific parameters that define the format of a CSV file, such as the
        delimiter, quote character, etc. "excel" is a commonly used default
        dialect that uses a comma as the delimiter and a double quote as the
        quote character.

    @param mode
        The mode to open the file, only "w" or "a" are supported. The default is
        "w".

    @param encoding
        Specify the output encoding, usually specified as "UTF-8". The default
        encoding is based on the platform, call
        `locale.getpreferredencoding(False)` to get the current locale encoding.
        See the `codecs` module for a list of supported encodings.

    @param delimiter:
        The character used to separate fields. The default in the "excel"
        dialect is a comma.

    @param quotechar:
        The character used to quote fields. The default in the "excel" dialect
        is a double quote.

    @param escapechar:
        The character used to escape field content, default is None. If a field
        contains the delimiter or quote character, the escape character can be
        used to avoid ambiguity.

    @param doublequote:
        If True (the default), quote characters in fields will be doubled. For
        example, "Hello, World" will be written as \"""Hello, World\""".

    @param skipinitialspace:
        If True, whitespace immediately following the delimiter is ignored. The
        default is False.

    @param lineterminator:
        The string used to terminate lines. The default is "\r\n", i.e.,
        carriage return plus line feed.

    @param quoting:
        Controls when quotes should be generated by the writer and recognized by
        the reader. It can be any of the following values:
            0: Indicates that quotes should only be used when necessary (for
               example, when the field contains the delimiter or quote
               character);
            1: Indicates that quotes should always be used;
            2: Indicates that quotes should never be used;
            3: Indicates that double quotes should always be used.

    @param strict:
        If True, raise errors for CSV format anomalies (such as extra quote
        characters). The default is False, which does not raise errors.
    """

    def __init__(self, file: File, /):
        self.file = file

    def reader(
            self,
            dialect:          Optional[CSVDialectLike] = None,
            *,
            delimiter:        Optional[str]            = None,
            quotechar:        Optional[str]            = None,
            escapechar:       Optional[str]            = None,
            doublequote:      Optional[bool]           = None,
            skipinitialspace: Optional[bool]           = None,
            lineterminator:   Optional[str]            = None,
            quoting:          Optional[int]            = None,
            strict:           Optional[bool]           = None
    ) -> CSVReader: ...

    def writer(
            self,
            dialect:          Optional[CSVDialectLike]    = None,
            *,
            mode:             Optional[Literal['w', 'a']] = None,
            encoding:         Optional[str]               = None,
            delimiter:        Optional[str]               = None,
            quotechar:        Optional[str]               = None,
            escapechar:       Optional[str]               = None,
            doublequote:      Optional[bool]              = None,
            skipinitialspace: Optional[bool]              = None,
            lineterminator:   Optional[str]               = None,
            quoting:          Optional[int]               = None,
            strict:           Optional[bool]              = None
    ) -> CSVWriter: ...


class JSON:
    """
    A class for handling JSON operations with a file object. It provides
    methods for loading JSON data from a file and dumping Python objects into a
    file as JSON.

    @param cls
        Pass a class used for decoding or encoding JSON data. By default,
        `json.JSONDecoder` is used for decoding (`self.load`), and
        `json.JSONEncoder` is used for encoding (`self.dump`). You can
        customize the decoding or encoding process by inheriting from these
        two classes and overriding their methods.

    @param object_hook
        This function will be used to decode dictionaries. It takes a dictionary
        as input, allows you to modify the dictionary or convert it to another
        type of object, and then returns it. This allows you to customize the
        data structure immediately after parsing JSON.

    @param parse_float
        This function will be used to decode floating-point numbers in JSON. By
        default, floating-point numbers are parsed into Python's float type. You
        can change this behavior by providing a custom function.

    @param parse_int
        This function will be used to decode integers in JSON. By default,
        integers are parsed into Python's int type. You can change this behavior
        by providing a custom function.

    @param parse_constant
        This function will be used to decode special constants in JSON (such as
        `Infinity`, `NaN`). By default, these constants are parsed into Python's
        `float("inf")` and `float("nan")`. You can change this behavior by
        providing a custom function.

    @param object_pairs_hook
        This function will be used to decode JSON objects. It takes a list of
        key-value pairs as input, allows you to convert these key-value pairs
        into another type of object, and then returns it. For example, you can
        use it to convert JSON objects to `gqylpy_dict.gdict`, which supports
        accessing and modifying key-value pairs in the dictionary using the dot
        operator.

    @param obj
        The Python object you want to convert to JSON format and write to the
        file.

    @param skipkeys
        If True (default is False), dictionary keys that are not of a basic
        type (str, int, float, bool, None) will be skipped during the encoding
        process.

    @param ensure_ascii
        If True (default), all non-ASCII characters in the output will be
        escaped. If False, these characters will be output as-is.

    @param check_circular
        If True (default), the function will check for circular references in
        the object and raise a `ValueError` if found. If False, no such check
        will be performed.

    @param allow_nan
        If True (default), `NaN`, `Infinity`, and `-Infinity` will be encoded as
        JSON. If False, these values will raise a `ValueError`.

    @param indent
        Specifies the number of spaces for indentation for prettier output. If
        None (default), the most compact representation will be used.

    @param separators
        A `(item_separator, key_separator)` tuple used to specify separators.
        The default separators are `(", ", ": ")`. If the `indent` parameter is
        specified, this parameter will be ignored.

    @param default
        A function that will be used to convert objects that cannot be
        serialized. This function should take an object as input and return a
        serializable version.

    @param sort_keys
        If True (default is False), the output of dictionaries will be sorted by
        key order.
    """

    def __init__(self, file: File, /):
        self.file = file

    def load(
            self,
            *,
            cls:               Optional[Type['json.JSONDecoder']] = None,
            object_hook:       Optional[JsonObjectHook]           = None,
            parse_float:       Optional[JsonObjectParse]          = None,
            parse_int:         Optional[JsonObjectParse]          = None,
            parse_constant:    Optional[JsonObjectParse]          = None,
            object_pairs_hook: Optional[JsonObjectPairsHook]      = None
    ) -> Any: ...

    def dump(
            self,
            obj:            Any,
            *,
            skipkeys:       Optional[bool]                     = None,
            ensure_ascii:   Optional[bool]                     = None,
            check_circular: Optional[bool]                     = None,
            allow_nan:      Optional[bool]                     = None,
            cls:            Optional[Type['json.JSONEncoder']] = None,
            indent:         Optional[Union[int, str]]          = None,
            separators:     Optional[Tuple[str, str]]          = None,
            default:        Optional[Callable[[Any], Any]]     = None,
            sort_keys:      Optional[bool]                     = None,
            **kw
    ) -> None: ...


class YAML:
    """
    A class for handling YAML operations with a file object. It provides
    methods for loading YAML data from a file and dumping Python objects into a
    file as YAML.

    @param loader
        Specify a loader class to control how the YAML stream is parsed.
        Defaults to `yaml.SafeLoader`. The YAML library provides different
        loaders, each with specific uses and security considerations.

        `yaml.FullLoader`:
            This is the default loader that can load the full range of YAML
            functionality, including arbitrary Python objects. However, due to
            its ability to load arbitrary Python objects, it may pose a security
            risk as it can load and execute arbitrary Python code.

        `yaml.SafeLoader`:
            This loader is safe, allowing only simple YAML tags to be loaded,
            preventing the execution of arbitrary Python code. It is suitable
            for loading untrusted or unknown YAML content.

        `yaml.Loader` & `yaml.UnsafeLoader`:
            These loaders are similar to `FullLoader` but provide fewer security
            guarantees. They allow loading of nearly all YAML tags, including
            some that may execute arbitrary code.

        Through this parameter, you can choose which loader to use to balance
        functionality and security. For example, if you are loading a fully
        trusted YAML file and need to use the full range of YAML functionality,
        you can choose `yaml.FullLoader`. If you are loading an unknown or not
        fully trusted YAML file, you should choose `yaml.SafeLoader` to avoid
        potential security risks.

    @param documents
        A list of Python objects to serialize as YAML. Each object will be
        serialized as a YAML document.

    @param dumper
        An instance of a Dumper class used to serialize documents. If not
        specified, the default `yaml.Dumper` class will be used.

    @param default_style
        Used to define the style for strings in the output, default is None.
        Options include ("|", ">", "|+", ">+"). Where "|" is used for literal
        style and ">" is used for folded style.

    @param default_flow_style
        A boolean value, default is False, specifying whether to use flow style
        by default. Flow style is a compact representation that does not use the
        traditional YAML block style for mappings and lists.

    @param canonical
        A boolean value specifying whether to output canonical YAML. Canonical
        YAML output is unique and does not depend on the Python object's
        representation.

    @param indent
        Used to specify the indentation level for block sequences and mappings.
        The default is 2.

    @param width
        Used to specify the width for folded styles. The default is 80.

    @param allow_unicode
        A boolean value specifying whether Unicode characters are allowed in the
        output.

    @param line_break
        Specifies the line break character used in block styles. Can be None,
        "\n", "\r", or "\r\n".

    @param encoding
        Specify the output encoding, usually specified as "UTF-8". The default
        encoding is based on the platform, call
        `locale.getpreferredencoding(False)` to get the current locale encoding.
        See the `codecs` module for a list of supported encodings.

    @param explicit_start
        A boolean value specifying whether to include a YAML directive (`%YAML`)
        in the output.

    @param explicit_end
        A boolean value specifying whether to include an explicit document end
        marker (...) in the output.

    @param version
        Used to specify the YAML version as a tuple. Can be, for example,
        `(1, 0)`, `(1, 1)`, or `(1, 2)`.

    @param tags
        A dictionary used to map Python types to YAML tags

    @param sort_keys
        A boolean value specifying whether to sort the keys of mappings in the
        output. The default is True.
    """

    def __init__(self, file: File, /):
        self.file = file

    def load(self, loader: Optional['YamlLoader'] = None) -> Any: ...

    def load_all(
            self, loader: Optional['YamlLoader'] = None
    ) -> Iterator[Any]: ...

    def dump(
            self,
            data: Any,
            /,
            dumper:             Optional['YamlDumper']      = None,
            *,
            default_style:      Optional[str]               = None,
            default_flow_style: Optional[bool]              = None,
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
            sort_keys:          Optional[bool]              = None
    ) -> None: ...

    def dump_all(
            self,
            documents:          Iterable[Any],
            /,
            dumper:             Optional['YamlLoader']      = None,
            *,
            default_style:      Optional[YamlDumpStyle]     = None,
            default_flow_style: Optional[bool]              = None,
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
            sort_keys:          Optional[bool]              = None
    ) -> None: ...


class SystemPath(Directory, File):

    def __init__(
            self,
            root: Optional[PathLink] = None,
            /, *,
            autoabs: Optional[bool] = None,
            strict: Optional[bool] = None
    ):
        """
        @param root
            A path link, hopefully absolute. If it is a relative path, the
            current working directory is used as the parent directory (the
            return value of `os.getcwd()`). The default value is also the return
            value of `os.getcwd()`.

        @param autoabs
            Automatically normalize the path link and convert to absolute path,
            at initialization. The default is False. It is always recommended
            that you enable the parameter when the passed path is a relative
            path.

        @param strict
            Set to True to enable strict mode, which means that the passed path
            must exist, otherwise raise `SystemPathNotFoundError` (or other).
            The default is False.
        """
        super().__init__(root, autoabs=autoabs, strict=strict)


class _xe6_xad_x8c_xe7_x90_xaa_xe6_x80_xa1_xe7_x8e_xb2_xe8_x90_x8d_xe4_xba_x91:
    gpack = globals()
    gpath = f'{__name__}.i {__name__}'
    gcode = __import__(gpath, fromlist=...)

    for gname in gpack:
        if gname[0] != '_':
            gfunc = getattr(gcode, gname, None)
            if gfunc and getattr(gfunc, '__module__', None) == gpath:
                gfunc.__module__ = __package__
                gfunc.__doc__ = gpack[gname].__doc__
                gpack[gname] = gfunc

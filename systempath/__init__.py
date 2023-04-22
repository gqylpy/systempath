"""(OOP) Operating system paths and files.

Let Python operating system paths and files become Simple, Simpler, Simplest,
Humanization, Unification, Flawless.

    >>> from systempath import SystemPath, Directory, File

    >>> root = SystemPath('/')

    >>> home: Directory = root['home']['gqylpy']
    >>> home
    /home/gqylpy

    >>> file: File = home['alpha.txt']
    >>> file
    /home/gqylpy/alpha.txt

    >>> file.open.rb().read()
    b'GQYLPY \xe6\x94\xb9\xe5\x8f\x98\xe4\xb8\x96\xe7\x95\x8c'

    @version: 1.0.7
    @author: 竹永康 <gqylpy@outlook.com>
    @source: https://github.com/gqylpy/systempath

────────────────────────────────────────────────────────────────────────────────
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
import os
import sys

from typing import (
    TypeVar, Literal, Optional, Union, Tuple, List, BinaryIO, TextIO, Callable,
    Generator, Iterator
)

BytesOrStr = TypeVar('BytesOrStr', bytes, str)
PathLink   = BytesOrStr

__all__ = ['SystemPath', 'Path', 'Directory', 'File', 'Open', 'Content', 'tree']


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
            at initialization. Default False. It is always recommended that you
            enable the parameter when the passed path is a relative path.

        @param strict
            Set to True to enable strict mode, which means that the passed path
            must exist, otherwise raise `SystemPathNotFoundError` (or other).
            Default False.

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

            Used to indicate whether symbolic links are followed, default True.
            If specified as False, and the last element of the parameter `path`
            is a symbolic link, the action will point to the symbolic link
            itself, not to the path to which the link points.

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

    def __eq__(self, other: ['Path', PathLink], /) -> bool:
        """Return True if the absolute path of the path instance is equal to the
        absolute path of another path instance (can also be a path link
        character) else False."""

    def __ne__(self, other: ['Path', PathLink], /) -> bool:
        return not self.__eq__(other)

    @property
    def basename(self) -> BytesOrStr:
        return os.path.basename(self.name)

    @property
    def dirname(self) -> 'Directory':
        return Directory(
            os.path.dirname(self.name),
            strict         =self.strict,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def dirnamel(self, level: int) -> 'Directory':
        """Like `self.dirname`, and can specify the directory level."""
        return Directory(
            self.name.rsplit(os.sep, maxsplit=level)[0],
            strict         =self.strict,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    @property
    def abspath(self) -> 'Path':
        return self.__class__(
            os.path.abspath(self.name),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def realpath(self, *, strict: Optional[bool] = None) -> 'Path':
        return self.__class__(
            os.path.realpath(self.name, strict=strict),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def relpath(self, start: Optional[PathLink] = None) -> 'Path':
        return self.__class__(
            os.path.relpath(self.name, start=start),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def normpath(self) -> 'Path':
        return self.__class__(
            os.path.normpath(self.name),
            strict         =self.strict,
            dir_fd         =self.dir_fd,
            follow_symlinks=self.follow_symlinks
        )

    def expanduser(self) -> 'Path':
        return self.__class__(
            os.path.expanduser(self.name),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def expandvars(self) -> 'Path':
        return self.__class__(
            os.path.expandvars(self.name),
            strict         =self.strict,
            follow_symlinks=self.follow_symlinks
        )

    def split(self) -> Tuple[PathLink, BytesOrStr]:
        return os.path.split(self.name)

    def splitdrive(self) -> Tuple[BytesOrStr, PathLink]:
        return os.path.splitdrive(self.name)

    @property
    def isabs(self) -> bool:
        return os.path.isabs(self.name)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.name)

    @property
    def lexists(self) -> bool:
        """Like `self.exists`, but do not follow symbolic links, return True for
        broken symbolic links."""
        return os.path.lexists(self.name)

    @property
    def isdir(self) -> bool:
        return os.path.isdir(self.name)

    @property
    def isfile(self) -> bool:
        return os.path.isfile(self.name)

    @property
    def islink(self) -> bool:
        return os.path.islink(self.name)

    @property
    def ismount(self) -> bool:
        return os.path.ismount(self.name)

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
            ignore_errors: Optional[bool]     = None,
            onerror:       Optional[Callable] = None
    ) -> None:
        """
        Delete the path, if the path is a file then call `os.remove` internally,
        if the path is a directory call `shutil.rmtree` internally.

        @param ignore_errors
            If the path does not exist will raise `FileNotFoundError`, can set
            this parameter to True to silence the exception. Default False.

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
            dst:           Union['Path', PathLink],
            /, *,
            copy_function: Optional[Callable[[PathLink, PathLink], None]] = None
    ) -> Union['Path', PathLink]:
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
            self, dst: Union['Path', PathLink], /
    ) -> Union['Path', PathLink]:
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
            self, dst: Union['Path', PathLink], /
    ) -> Union['Path', PathLink]:
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
            self, dst: Union['Path', PathLink], /
    ) -> Union['Path', PathLink]:
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
        """Get the size of the file, Return 0 if the path is a directory."""
        return os.path.getsize(self.name)

    def getctime(self) -> float:
        return os.path.getctime(self.name)

    def getmtime(self) -> float:
        return os.path.getmtime(self.name)

    def getatime(self) -> float:
        return os.path.getatime(self.name)

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
            Default False, this parameter may not be available on your platform,
            using them will ignore if unavailable. You can look up `os.access`
            for more description.

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
            Set the flag for the file or directory, different flag have different
            attributes. Call `os.chflags` internally.

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

    def __getitem__(
            self, name: BytesOrStr
    ) -> Union['SystemPath', 'Directory', 'File', Path]:
        path: PathLink = os.path.join(self.name, name)

        if self.strict:
            if os.path.isdir(path):
                return Directory(path, strict=self.strict)
            if os.path.isfile(path):
                return File(path)
            if os.path.exists(name):
                return Path(name)
            else:
                raise SystemPathNotFoundError
        else:
            return SystemPath(path)

    def __delitem__(self, name: BytesOrStr) -> None:
        Path(os.path.join(self.name, name)).delete()

    def __iter__(self) -> Generator:
        return self.subpaths

    @staticmethod
    def home(
            *,
            strict:          Optional[bool] = None,
            follow_symlinks: Optional[bool] = None
    ) -> 'Directory':
        return Directory(
            '~', strict=strict, follow_symlinks=follow_symlinks
        ).expanduser()

    @property
    def subpaths(self) -> Generator:
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
            level:      Optional[int]  = None,
            bottom_up:  Optional[bool] = None,
            omit_dir:   Optional[bool] = None,
            mysophobia: Optional[bool] = None,
            shortpath:  Optional[bool] = None
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
            self,
            *,
            topdown: Optional[bool]     = None,
            onerror: Optional[Callable] = None
    ) -> Iterator[Tuple[PathLink, List[BytesOrStr], List[BytesOrStr]]]:
        """
        Directory tree generator, recurse the directory to get all
        subdirectories and files, yield a 3-tuple for each subdirectory, call
        `os.walk` internally.

        The yielding 3-tuple is as follows:
            (current_directory_path, all_subdirectory_names, all_file_names)

        @param topdown
            Default True, generate the directory tree from the outside in. If
            specified as False, from the inside out.

        @param onerror
            An optional error handler, for more instructions see `os.walk`.
        """

    def copytree(
            self,
            dst:                      Union['Directory', PathLink],
            /, *,
            symlinks:                 Optional[bool]                     = None,
            ignore: Optional[Callable[
                [PathLink, List[BytesOrStr]], List[BytesOrStr]]]         = None,
            copy_function: Optional[Callable[[PathLink, PathLink], None]]
                                                                         = None,
            ignore_dangling_symlinks: Optional[bool]                     = None,
            dirs_exist_ok:            Optional[bool]                     = None
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
            Default False.

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
            parameter `symlinks`. Default False. This parameter has no effect on
            platforms that do not support `os.symlink`.

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
            mode:          Optional[int]  = None,
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
            silently skip. Default False.
        """

    def makedirs(
            self,
            mode:     Optional[int]  = None,
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
            set this parameter to True to silence the exception. Default False.
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
            ignore_errors: Optional[bool]     = None,
            onerror:       Optional[Callable] = None
    ) -> None:
        """
        Delete the directory tree recursively, call `shutil.rmtree` internally.

        @param ignore_errors
            If the directory does not exist will raise `FileNotFoundError`, can
            set this parameter to True to silence the exception. Default False.

        @param onerror
            An optional error handler, described more see `shutil.rmtree`.
        """

    def chdir(self) -> None:
        """Change the working directory of the current process to the directory.
        """
        os.chdir(self.name)


class File(Path):
    """Pass a file path link to get a file object, which you can then use to do
    anything a file can do."""

    @property
    def open(self) -> 'Open':
        return Open(self)

    content = property(
        lambda self         : self.contents.read(),
        lambda self, content: self.contents.overwrite(content),
        lambda self         : self.contents.clear(),
        """Quickly read, rewrite, or empty all contents of the file (in binary
        mode)."""
    )

    @property
    def contents(self) -> 'Content':
        """Operation the file content, super version of `self.content`."""
        return Content(self.name)

    @contents.setter
    def contents(self, content: ['Content', bytes]) -> None:
        """Do nothing, syntax hints for compatibility with `Content.__iadd__`
        and `Content.__ior__` only."""

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return os.path.splitext(self.name)

    @property
    def extension(self) -> BytesOrStr:
        return os.path.splitext(self.name)[1]

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
            dst:     Union['File', BinaryIO],
            /, *,
            bufsize: Optional[int]           = None
    ) -> Union['File', BinaryIO]:
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

    def truncate(self, length: int) -> None:
        os.truncate(self.name, length)

    def clear(self) -> None:
        self.truncate(0)

    def mknod(
            self,
            mode:          Optional[int]  = None,
            *,
            device:        Optional[int]  = None,
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
            silently skip. Default False.
        """

    def mknods(
            self,
            mode:          Optional[int]  = None,
            *,
            device:        Optional[int]  = None,
            ignore_exists: Optional[bool] = None
    ) -> None:
        """Create the file and all intermediate paths, super version of
        `self.mknod`."""
        self.dirname.makedirs(mode, exist_ok=True)
        self.mknod(mode, device=device, ignore_exists=ignore_exists)

    def remove(self, *, ignore_errors: Optional[bool] = None) -> None:
        """
        Remove the file, call `os.remove` internally.

        @param ignore_errors
            If the file does not exist will raise `FileNotFoundError`, can set
            this parameter to True to silence the exception. Default False.
        """

    def unlink(self) -> None:
        """Remove the file, like `self.remove`, call `os.unlink` internally."""


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
        newline character, default False.

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
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def wb(
            self,
            *,
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def xb(
            self,
            *,
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def ab(
            self,
            *,
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def rb_plus(
            self,
            *,
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def wb_plus(
            self,
            *,
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def xb_plus(
            self,
            *,
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def ab_plus(
            self,
            *,
            bufsize: Optional[int]                            = None,
            opener:  Optional[Callable[[PathLink, int], int]] = None
    ) -> BinaryIO: ...

    def r(
            self,
            *,
            bufsize:  Optional[int]                             = None,
            encoding: Optional[str]                             = None,
            errors:   Optional[str]                             = None,
            newline:  Optional[Literal['', '\n', '\r', '\r\n']] = None,
            opener:   Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def w(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[str]                             = None,
            newline:        Optional[Literal['', '\n', '\r', '\r\n']] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def x(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[str]                             = None,
            newline:        Optional[Literal['', '\n', '\r', '\r\n']] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def a(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[str]                             = None,
            newline:        Optional[Literal['', '\n', '\r', '\r\n']] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def r_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[str]                             = None,
            newline:        Optional[Literal['', '\n', '\r', '\r\n']] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def w_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[str]                             = None,
            newline:        Optional[Literal['', '\n', '\r', '\r\n']] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def x_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[str]                             = None,
            newline:        Optional[Literal['', '\n', '\r', '\r\n']] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def a_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[str]                             = None,
            newline:        Optional[Literal['', '\n', '\r', '\r\n']] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...


class Content:
    """Pass in an instance of `File` (or a file path link) to get a file content
    object, which you can then use to operation the contents of the file (in
    binary mode)."""

    def __init__(self, file: Union[File, PathLink], /):
        self.file = file

    def __bytes__(self) -> bytes:
        return self.read()

    def __ior__(self, content: Union['Content', bytes], /) -> 'Content':
        self.overwrite(content)
        return self

    def __iadd__(self, content: Union['Content', bytes], /) -> 'Content':
        self.append(content)
        return self

    def __eq__(self, content: Union['Content', bytes], /) -> bool:
        """Whether the current file content equals the another file content (or
        a bytes object)."""

    def __ne__(self, content: Union['Content', bytes], /) -> bool:
        """Whether the current file content is not equal to another file content
        (or a byte object)."""

    def __iter__(self) -> Generator:
        """Iterate over the file by line, omitting newline symbol and ignoring
        the last blank line."""

    def __len__(self) -> int:
        """Return the length (actually the size) of the file contents."""

    def __bool__(self) -> bool:
        """Return True if the file has content, False otherwise."""

    def read(self, size: int = -1, /) -> bytes:
        return Open(self.file).rb().read(size)

    def overwrite(self, content: Union['Content', bytes], /) -> None:
        """Overwrite the current file content from another file content (or a
        bytes object)."""

    def append(self, content: Union['Content', bytes], /) -> None:
        """Append the another file contents (or a bytes object) to the current
        file."""

    def copy(
            self,
            dst:     Union['Content', BinaryIO],
            /, *,
            bufsize: Optional[int]              = None
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


def tree(
        dirpath:    Optional[PathLink] = None,
        /, *,
        level:      Optional[int]      = None,
        bottom_up:  Optional[bool]     = None,
        omit_dir:   Optional[bool]     = None,
        mysophobia: Optional[bool]     = None,
        shortpath:  Optional[bool]     = None
) -> Generator:
    """
    Directory tree generator, recurse the directory to get all subdirectories
    and files.

    @param dirpath
        Specify a directory path link, recurse this directory on call to get all
        subdirectories and files, default is current working directory (the
        return value of `os.getcwd()`).

    @param level
        Recursion depth of the directory, default is maximum recursive depth
        (the return value of `sys.getrecursionlimit()`). An int must be passed
        in, any integer less than 1 is considered to be 1, warning passing
        decimals can cause depth confusion.

    @param bottom_up
        By default, the outer path is yielded first, from which the inner path
        is yielded. If your requirements are opposite, set this parameter to
        True.

    @param omit_dir
        Omit all subdirectories when yielding paths. Default False.

    @param mysophobia
        By default, if the subpath is a directory then yield a `Directory`
        object, if the subpath is a file then yield a `File` object. If set this
        parameter to True, directly yield the path link string (or bytes). This
        parameter is not recommended for use.

    @param shortpath
        Yield short path link string, delete the `dirpath` from the left end of
        the path, used with the parameter `mysophobia`. Default False.
    """


class SystemPath(Directory, File):

    def __init__(
            self,
            root:    Optional[PathLink] = None,
            /, *,
            autoabs: Optional[bool]     = None,
            strict:  Optional[bool]     = None
    ):
        super().__init__(
            '.' if root in (None, '') else b'.' if root == b'' else root,
            autoabs=autoabs,
            strict =strict
        )


class _xe6_xad_x8c_xe7_x90_xaa_xe6_x80_xa1_xe7_x8e_xb2_xe8_x90_x8d_xe4_xba_x91:
    gpath = f'{__name__}.i {__name__}'
    __import__(gpath)

    gpack = sys.modules[__name__]
    gcode = globals()[f'i {__name__}']

    for gname in globals():
        try:
            assert gname[0] != '_'
            gfunc = getattr(gcode, gname)
            assert gfunc.__module__ == gpath
        except (AssertionError, AttributeError):
            continue
        gfunc.__module__ = __package__
        gfunc.__doc__ = getattr(gpack, gname).__doc__
        setattr(gpack, gname, gfunc)

"""
Make Python operation files and system paths become Simple, Simpler, Simplest,
Humanized, Unified, Flawless.

    @version: 1.0.alpha6
    @author: 竹永康 <gqylpy@outlook.com>
    @source: https://github.com/gqylpy/gqylpy-filesystem

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
    Literal, Optional, Union, Tuple, List, BinaryIO, TextIO, Callable
)

BytesOrStr = Union[bytes, str]
PathLink   = BytesOrStr

EncodingErrorHandlingMode = Literal[
    'strict',
    'ignore',
    'replace',
    'surrogateescape',
    'xmlcharrefreplace',
    'backslashreplace',
    'namereplace'
]


class File:
    """Pass a file path to get a file object, which you can then use to do
    anything a file can do."""

    def __init__(
            self,
            path:            PathLink,
            /, *,
            follow_symlinks: Optional[bool] = None,
            dir_fd:          Optional[int]  = None
    ):
        """
        @param path
            A file path, hopefully absolute. If it is a relative path, the
            current working directory is used as the parent directory (the
            return value of `os.getcwd()`).

        @param follow_symlinks
            This optional parameter applies only to the following methods:
                `readable`, `writeable`, `executable`, `copy`,
                `copystat`, `copymode`,  `link`,       `stat`,
                `chmod`,    `access`,    `lchmod`,     `chown`,
                `chflags`,  `getxattr`,  `listxattr`,  `removexattr`

            Used to indicate whether symbolic links are followed, default True.
            If specified as False, and the last element of the parameter `path`
            is a symbolic link, the action will point to the symbolic link
            itself, not to the file to which the link points.

            This parameter may not be available on your platform, using them
            will raise `NotImplementedError` if unavailable.

        @param dir_fd
            This optional parameter applies only to the following methods:
                `readable`, `writeable`, `executable`, `rename`,
                `replace`,  `link`,      `symlink`,    `mknod` (not on Windows),
                `stat`,     `lstat`,     `chmod`,      `access`,
                `lchmod`,   `chown`

            A file descriptor open to a directory, obtain by `os.open`, sample
            `os.open('dir/', os.O_RDONLY)`. If this parameter is specified and
            the parameter `path` is relative, the parameter `path` will then be
            relative to that directory; otherwise, this parameter is ignored.

            This parameter may not be available on your platform, using them
            will ignore or raise `NotImplementedError` if unavailable.
        """
        self.path            = path
        self.dir_fd          = dir_fd
        self.follow_symlinks = follow_symlinks

    @property
    def open(self) -> 'Open':
        return Open(self)

    @property
    def name(self) -> PathLink:
        return self.path

    @property
    def basename(self) -> BytesOrStr:
        return os.path.basename(self.path)

    @property
    def dirname(self) -> PathLink:
        return os.path.dirname(self.path)

    def dirnamel(self, level: int) -> PathLink:
        """Like `self.dirname`, and can specify the directory level."""
        return self.path.rsplit(os.sep, maxsplit=level)[0]

    @property
    def abspath(self) -> PathLink:
        return os.path.abspath(self.path)

    realpath = abspath

    def relpath(self, start: Optional[PathLink] = None):
        return os.path.relpath(self.path, start=start)

    def split(self) -> Tuple[PathLink, BytesOrStr]:
        return os.path.split(self.path)

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return os.path.splitext(self.path)

    @property
    def extension(self) -> BytesOrStr:
        return os.path.splitext(self.path)[1]

    def splitdrive(self) -> Tuple[BytesOrStr, PathLink]:
        return os.path.splitdrive(self.path)

    @property
    def isabs(self) -> bool:
        return os.path.isabs(self.path)

    @property
    def isfile(self) -> bool:
        return os.path.isfile(self.path)

    @property
    def exists(self) -> bool:
        return os.path.exists(self.path)

    @property
    def lexists(self) -> bool:
        """Like `self.exists`, but do not follow symbolic links, return True for
        broken symbolic links."""
        return os.path.lexists(self.path)

    @property
    def islink(self) -> bool:
        return os.path.islink(self.path)

    @property
    def readable(self) -> bool:
        return self.access(os.R_OK)

    @property
    def writeable(self) -> bool:
        return self.access(os.W_OK)

    @property
    def executable(self) -> bool:
        return self.access(os.X_OK)

    def rename(self, dst: PathLink, /) -> PathLink:
        """
        Rename the file, call `os.rename` internally.

        The optional initialization parameter `self.dir_fd` will be passed to
        parameters `src_dir_fd` and `dst_dir_fd` of `os.rename`.

        Important Notice:
        If the destination path is relative and is a single name, the parent
        path of the source is used as the parent path of the destination instead
        of using the current working directory, different from the traditional
        way.

        Backstory about providing this method
            https://github.com/gqylpy/gqylpy-filesystem/issues/1

        @return: The destination path.
        """

    def renames(self, dst: PathLink, /) -> PathLink:
        """
        Rename the file, super version of `self.rename`. Call `os.renames`
        internally.

        When renaming the file, the destination path is created if the
        destination path does not exist, including any intermediate directories;
        After renaming the file, the source path is deleted if it is empty,
        delete from front to back until the entire path is used or a nonempty
        directory is found.

        Important Notice:
        If the destination path is relative and is a single name, the parent
        path of the source is used as the parent path of the destination instead
        of using the current working directory, different from the traditional
        way.

        Backstory about providing this method
            https://github.com/gqylpy/gqylpy-filesystem/issues/1

        @return: The destination path.
        """

    def replace(self, dst: PathLink, /) -> PathLink:
        """
        Rename the file, overwrite if destination exists. Call `os.replace`
        internally.

        The optional initialization parameter `self.dir_fd` will be passed to
        parameters `src_dir_fd` and `dst_dir_fd` of `os.replace`.

        Important Notice:
        If the destination path is relative and is a single name, the parent
        path of the source is used as the parent path of the destination instead
        of using the current working directory, different from the traditional
        way.

        Backstory about providing this method
            https://github.com/gqylpy/gqylpy-filesystem/issues/1

        @return: The destination path.
        """

    def move(
            self,
            dst:           Union['File', PathLink],
            /, *,
            copy_function: Optional[Callable[[PathLink, PathLink], None]] = None
    ) -> Union['File', PathLink]:
        """
        Move the file to another location, similar to the Unix system `mv`
        command. Call `shutil.move` internally.

        @param dst:
            Where to move the file, hopefully pass in an instance of `File`, can
            also pass in a file path link.

        @param copy_function
            The optional parameter `copy_function` will be passed to
            `shutil.move` and default value is `shutil.copy2`.

        Backstory about providing this method
            https://github.com/gqylpy/gqylpy-filesystem/issues/1

        @return: The parameter `dst` is passed in, without any modification.
        """

    def copy(self, dst: Union['File', PathLink], /) -> Union['File', PathLink]:
        """
        Copy the file to another file, call `shutil.copyfile` internally.

        @param dst:
            Where to copy the file, hopefully pass in an instance of `File`, can
            also pass in a file path link.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the file path is a symbolic
        link, will create a new symbolic link instead of copy the file to which
        the link points to.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def copystat(
            self, dst: Union['File', PathLink], /
    ) -> Union['File', PathLink]:
        """
        Copy the file metadata to another file, call `shutil.copystat`
        internally.

        @param dst:
            Where to copy the file metadata, hopefully pass in an instance of
            `File`, can also pass in a file path link.

        The copied metadata includes permission bits, last access time, and last
        modification time. On Unix, extended attributes are also copied where
        possible. The file contents, owner, and group are not copied.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, the action will point to the symbolic link itself,
        not to the file to which the link points, if and only if both the
        initialization parameter `self.path` and the parameter `dst` are
        symbolic links.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def copymode(
            self, dst: Union['File', PathLink], /
    ) -> Union['File', PathLink]:
        """
        Copy the file mode bits to another file, call `shutil.copymode`
        internally.

        @param dst:
            Where to copy the file mode bits, hopefully pass in an instance of
            `File`, can also pass in a file path link.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, the action will point to the symbolic link itself,
        not to the file to which the link points, if and only if both the
        initialization parameter `self.path` and the parameter `dst` are
        symbolic links. But if `self.lchmod` isn't available (e.g. Linux) this
        method does nothing.

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
            Where to copy the file contents, hopefully pass in an instance
            of `File`. Can also pass in a stream of the destination file (or
            called handle), it must have at least writable or append permission.

        @param bufsize
            The buffer size, the length of each copy, default is 64K (if your
            platform is Windows then 1M). Passing -1 turns off buffering.

        @return: The parameter `dst` is passed in, without any modification.
        """

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

    def symlink(
            self, dst: Union['File', PathLink], /
    ) -> Union['File', PathLink]:
        """
        Create a symbolic link to the file, call `os.symlink` internally.

        @param dst:
            Where to create the symbolic link for the file, hopefully pass in an
            instance of `File`, can also pass in a file path link.

        @return: The parameter `dst` is passed in, without any modification.
        """

    def readlink(self) -> PathLink:
        """
        Return the file path to which the symbolic link points.

        If the initialization parameter `self.path` is not a symbolic link, call
        this method will raise `OSError`.
        """

    def truncate(self, length: int) -> None:
        os.truncate(self.path, length)

    def clear(self) -> None:
        self.truncate(0)

    def mknod(
            self,
            mode:          int  = None,
            *,
            device:        int  = None,
            ignore_exists: bool = None
    ) -> None:
        """
        Create the file, call `os.mknod` internally, but if your platform is
        Windows then internally call `io.FileIO(self.path, 'x')`.

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

    def remove(self) -> None:
        os.remove(self.path, dir_fd=self.dir_fd)

    def unlink(self) -> None:
        os.unlink(self.path, dir_fd=self.dir_fd)

    @property
    def stat(self) -> os.stat_result:
        """
        Get the file status, perform a stat system call against the file. Call
        `os.stat` internally.

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the path is a symbolic link,
        the action will point to the symbolic link itself, not to the file to
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
        """Get the file status, like `self.stat`, but do not follow symbolic
        links."""
        return File(
            self.path, follow_symlinks=False, dir_fd=self.dir_fd
        ).stat

    def getsize(self) -> int:
        return os.path.getsize(self.path)

    def getctime(self) -> float:
        return os.path.getctime(self.path)

    def getmtime(self) -> float:
        return os.path.getmtime(self.path)

    def getatime(self) -> float:
        return os.path.getatime(self.path)

    def chmod(self, mode: int, /) -> None:
        """
        Change the access permissions of the file, call `os.chmod` internally.

        @param mode
            Specify the access permissions of the file, can be a permission
            mask (0o600), can be a combination (0o600|stat.S_IFREG), can be a
            bitwise (33152).

        If the optional initialization parameter `self.follow_symlinks` is
        specified as False, and the last element of the path is a symbolic link,
        the action will point to the symbolic link itself, not to the file to
        which the link points.
        """

    def access(
            self, mode: int, /, *, effective_ids: Optional[bool] = None
    ) -> bool:
        """
        Test the file access permissions with the real uid/gid, call `os.access`
        internally.

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
        the action will point to the symbolic link itself, not to the file to
        which the link points.
        """

    if sys.platform != 'win32':
        def lchmod(self, mode: int, /) -> None:
            """Change the access permissions of the file, like `self.chmod`, but
            do not follow symbolic links."""
            File(self.path, follow_symlinks=False).chmod(mode)

        def chown(self, uid: int, gid: int) -> None:
            """
            Change the file owner and owner group, call `os.chown` internally.

            @param uid
                Specify the owner id of the file, obtain by `os.getuid()`.

            @param gid
                Specify the owner group id of the file, obtain by `os.getgid()`.

            If the optional initialization parameter `self.follow_symlinks` is
            specified as False, and the last element of the path is a symbolic
            link, the action will point to the symbolic link itself, not to the
            file to which the link points.
            """

        def lchown(self, uid: int, gid: int) -> None:
            """Change the file owner and owner group, like `self.chown`, but do
            not follow symbolic links."""
            File(self.path, follow_symlinks=False).chown(uid, gid)

        def chflags(self, flags: int) -> None:
            """"
            Set the flag for the file, different flag have different attributes.
            Call `os.chflags` internally.

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
            file to which the link points.

            Warning, do not attempt to set flags for important files in your
            system, this may cause your system failure, unable to start!

            This method may not be available on your platform, using them will
            raise `NotImplementedError` if unavailable.
            """

        def lchflags(self, flags: int) -> None:
            """Like `self.chflags`, but do not follow symbolic links."""
            File(self.path, follow_symlinks=False).chflags(flags)

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            """
            Change the hidden attributes of the file, call the Unix system
            command `chattr` internally.

            @param operator
                Specify an operator "+", "-", or "=". Used with the parameter
                `attributes` to add, remove, or reset certain attributes.

            @param attrs
                a: Only data can be appended.
                A: Tell the system not to change the last access time to the
                   file. However, this attribute is automatically removed after
                   manual modification.
                c: Compress the file and save it.
                d: Exclude the file from the "dump" operation, the file is not
                   backed up by "dump" when the "dump" program is executed.
                e: Default attribute, this attribute indicates that the file is
                   using an extended partition to map blocks on disk.
                D: Check for errors in the compressed file.
                i: The file is not allowed to be modified.
                u: Prevention of accidental deletion, when the file is deleted,
                   the system retains the data block so that it can recover the
                   file later.
                s: As opposed to the attribute "u", when deleting the file, it
                   will be completely deleted (fill the disk partition with 0)
                   and cannot be restored.
                S: Update the file instantly.
                t: The tail-merging, file system support tail merging.
                ...
                More attributes that are rarely used (or no longer used), you
                can refer to the manual of the Unix system command `chattr`.

            Use Warning, the implementation of method `chattr` is to directly
            call the system command `chattr`, so this is very unreliable. Also,
            do not attempt to modify hidden attributes of important files in
            your system, this may cause your system failure, unable to start!
            """

        def lsattr(self) -> str:
            """
            Return the hidden attributes of the file, call the Unix system
            command `lsattr` internally.

            Use Warning, the implementation of method `lsattr` is to directly
            call the system command `lsattr`, so this is very unreliable.
            """

        def exattr(self, attr: str, /) -> bool:
            """Check whether the file has a hidden attribute and return True or
            False. The usage of parameter `attr` can be seen in method `chattr`.
            """
            return attr in self.lsattr()

        if sys.platform == 'linux':
            def getxattr(self, attribute: BytesOrStr, /) -> bytes:
                """Return the value of extended attribute on path, you can look
                up `os.getxattr` for more description."""

            def setxattr(
                    self,
                    attribute: BytesOrStr,
                    value:     bytes,
                    *,
                    flags:     Optional[int] = None
            ) -> None:
                """
                Set extended attribute on path to value, you can look up
                `os.setxattr` for more description.

                If the optional initialization parameter `self. follow_symlinks`
                is specified as False, and the last element of the path is a
                symbolic link, the action will point to the symbolic link
                itself, not to the file to which the link points.
                """

            def listxattr(self) -> List[str]:
                """
                Return a list of extended attributes on path, you can look up
                `os.listxattr` for more description.

                If the optional initialization parameter `self. follow_symlinks`
                is specified as False, and the last element of the path is a
                symbolic link, the action will point to the symbolic link
                itself, not to the file to which the link points.
                """

            def removexattr(self, attribute: BytesOrStr, /) -> None:
                """
                Remove extended attribute on path, you can look up
                `os.removexattr` for more description.

                If the optional initialization parameter `self. follow_symlinks`
                is specified as False, and the last element of the path is a
                symbolic link, the action will point to the symbolic link
                itself, not to the file to which the link points.
                """

    def md5(self, salting: Optional[bytes] = None) -> str:
        """Return the hex digest value of the file content."""


class Open:
    """
    Open a file and return a file stream (or called handle).

    >>> f: BinaryIO = Open('alpha.bin').rb()  # open for reading in binary mode.
    >>> f: TextIO   = Open('alpha.txt').r()   # open for reading in text mode.

    Pass in an instance of `File` (or a file path) at instantiation time. At
    instantiation time (do nothing) the file will not be opened, only when you
    call one of the following methods, the file will be opened (call once, open
    once), open mode equals method name (where method `rb_plus` equals mode
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
        Pass an integer greater than 0 to set the buffer size, and 1 in text
        mode to use line buffering. The buffer size is selected by default using
        a heuristic (reference `io.DEFAULT_BUFFER_SIZE`, on most OS, the buffer
        size is usually 8192 or 4096 bytes), for "interactive" text files (files
        for which call `isatty()` returns True), line buffering is used by
        default.

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
            errors:   Optional[EncodingErrorHandlingMode]       = None,
            newline:  Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            opener:   Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def w(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[EncodingErrorHandlingMode]       = None,
            newline:        Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def x(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[EncodingErrorHandlingMode]       = None,
            newline:        Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def a(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[EncodingErrorHandlingMode]       = None,
            newline:        Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def r_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[EncodingErrorHandlingMode]       = None,
            newline:        Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def w_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[EncodingErrorHandlingMode]       = None,
            newline:        Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def x_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[EncodingErrorHandlingMode]       = None,
            newline:        Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    def a_plus(
            self,
            *,
            bufsize:        Optional[int]                             = None,
            encoding:       Optional[str]                             = None,
            errors:         Optional[EncodingErrorHandlingMode]       = None,
            newline:        Optional[Literal["", "\n", "\r", "\r\n"]] = None,
            line_buffering: Optional[bool]                            = None,
            write_through:  Optional[bool]                            = None,
            opener:         Optional[Callable[[PathLink, int], int]]  = None
    ) -> TextIO: ...

    rt = r
    wt = w
    xt = x
    at = a
    rt_plus = r_plus
    wt_plus = w_plus
    xt_plus = x_plus
    at_plus = a_plus


class _xe6_xad_x8c_xe7_x90_xaa_xe6_x80_xa1_xe7_x8e_xb2_xe8_x90_x8d_xe4_xba_x91:
    """  QYYYQLLYYYYYYYQLYYQYYQQQYQQYQQQQQQQQQQQQQQQQQQQQQQYYYQQQQQQYL
        YYYYQYLLQYLLYYQYYYYYYYQQYQYQYQQQQQQQQQQQQQQQQQQQQQQQYYYQQQQQQ
        QYYYYLPQYLPLYYYLLYYYYYYYYQQQYQQQQQQQQQQQQQQQQQQQQQQQYYYYQQQQQP
        QYYQLPLQYLLYYQPLLLYYYYYYQYYQYQQQQQQQQQQQQQQYQQQQQQQQYYQYQQQQQQP
       QYYQYLLYYYLLYQYLLYYYYYYYYQYYQYQYYYQQQQQQQQQQYQQQQQQYQQYQYYQQQQQYP
      LQYQYYYYQYYYYYQYYYYYYYYYYYYYYYQQYYYYYYYYYQQQQYQQQQQQYQQYQYYQQQQQQ P
      QYQQYYYYQYYYQQQYYYYYYYYQYQYYYYQQYYYQYQYYQQQQYQQQQQQQYQQYQYYQQQQQQ P
      QYQQYYYYQYYYQQQYYYYYYYYQYQYYYYYQYYYYQYYYQQQQYQQQQQQQYQQYQQYQQQQYYP
      QYQYYYYYQYYYQQQ PYLLLYP PLYYYYYYQYYYYYYQQQQYYQQQQQQYQQYQQQYQQQQYQ
      PQQYYYYYQYYQQYQQQQQQQQQQYP        PPLYQYQYQYQLQQQQQYQQYQQQYYQQQYY
       QQYYYYYQQYQLYQQPQQQQQL QYL           PPYYLYYLQYQQYYQYQQQQYYQPQYL
       YQYYYYQQQYQ  LYLQQQQQQYQQ           YQQQQQGQQQQQQYQYYQQQQYQPQYQ P
      L QYYYYQQLYQ   Y YPYQQQQQ           LQQQQQL YQQQQYQQYQYQQYYQQYQP P
        YYQYYQQ  Q    LQQQQQQY            YQYQQQQQQYYQYLQYQQYQQYYQYQL P
     Y  LYQLQQPL Y     P  P                QLLQQQQQ Q  PQQQQYQQYYQQL P
    P   PYQYQQQQPQ                         PQQQQQQY    QQYQYYQQYYQPP
    L    QQQYQ YYYY              PQ           L  P    LPQYQYYQQLQ P
    Y   PPQQYYL LYQL                                 PQLQYQQYQYQ  L
    Y     QQYQPP PYQY        PQ                      Q  QQYQYQYL  L
    Y     QQYYQ L  QYQP         PLLLLLYL           LQQ LQYYQQQP P L
     L   PPLQYYQ Y  LQQQ                         LQYQ  QYYYQQ     P
      L    Q  QYQ  Y  QQPYL                   PQYYYYPPQYYQQQP    L
       L    L  PQQL   LYQ  PQP             QL PYYYPLQLYQ  QY P   Y
         P   P    PQQP  QY  QLLQQP   LYYLQ   PQYPQQQP P  QY P   L
                       PYQYYY           PQ  PQ      L   Q P    L
              PQYLYYYPQ PLPL             L QY YQYYQYLYQQQ    P
            PYLLLLLYYYQ P  L    P         PYL  PQYYLLLLLLLQ
           LYPLLLLLLYYYY   Y  YQY     LLLPPY   LYYYLLLLLLLLY
           YLLLYLLLLLLYYQ  Q              PQ  YYYLLLLLLLLLLYP
          YLLLLLLLLLLLLLLYQQ              PYYQYYLLLLLLLLYYYLQ
          QLLLLLLLLLLLLLLLLLYYQYP        YQYYLLLLLLLLLLLLLLLQ
          YLLLLLLLLLLLLLLLLLLLYYYLLYYYLLLLLLLLLLLLLLLLLLLLLLYP
         PLLLLLLLLLLLLLLLLLLLLLLLYLLLLLLLLLLLLLLLLLLLLLLLYLYLL
         LLLLLLLLLLYYLLLLLLYLLLLLLLLLLLLLLLL GQYLPY LLLYLYLLLY
         QLLLLYYLYLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLQYYYYLLQ
         QLLLLLYYQYLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLQLYYLLLQ
        LYLLYLLLQYYLLLLLLLLLLLLLLLLLLLLLLLLLLLLLYLLLLLQYYYYYLYQ
        YLLLYYLLYQYLLLLLLLLLLLLLLLLLLLLLLLLLLLLYLLLLLYYYYQLLLLY
        QLLLYYYYYQLLLLLLLLLLLLLLYLLLLLLLLLLLLLLLLLLLLYYYLQLLPLLQ
        YLYLLQYYYQLLLLLLLLLLLLLLLLLLLLLLLLLLLLYYLLLLLYYQYYLLLLLQ
       LYLLLLLYYYQLLYLLLLLLLLLLLLYLYLLYYLLLLYLLLLLLLYYYQQLLLLLLLY
       YLLLLLLYYYQLLYLLLLLLLYLYLLLLLLLLLLLLLLLLLLLLYYYYQQLYLLLLLQ
       QLLLYLLLQYQLQLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLYYYQYYLLLLLLLY
       QLLLLLLLLQQYQLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLQYYQYYLLLLLLLQ
       QLLLLLLLLLQQYLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLYYYYLLLLLLLLLYL
       QLLLLYLYYLYQLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLLQYYYLLLLLLLLLQ
       YLLLLLLLYYLQLLLLLLLLLLLLLLLLLLLLLLLLLYLLLLLLLLYQYYLLLLLLLLLQ
       QLLLLLYLYYYYLLLLLPLLLLLLLYLYLLLLLLLLLLLLLLLLLLLQYYLLLLLLLLYP
       YYLYYLLYYYQLLLLLLLLYLLLLLLLLLLLLLLLLLLLLLLYLYLLYQYYLLLLLLYL
        QLLLLLLYQYLLLLLLLLLLLLLLLLLLLLLYYLYLLLLLLLLLLLYQQQQQQQLYL  """
    gpath = f'{__name__}.g {__name__[7:]}'
    __import__(gpath)

    gpack = sys.modules[__name__]
    gcode = globals()[f'g {__name__[7:]}']

    for gname in globals():
        if gname[0] != '_':
            try:
                gfunc = getattr(gcode, gname)
                if gfunc.__module__ is gpath:
                    gfunc.__module__ = __package__
                    gfunc.__doc__ = getattr(gpack, gname).__doc__
                    setattr(gpack, gname, gfunc)
            except AttributeError:
                pass

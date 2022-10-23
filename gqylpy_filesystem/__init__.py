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

from typing import TextIO, Union, Literal, Tuple, Callable, Optional

PathLink = BytesOrStr = Union[bytes, str]


class File:

    def __init__(
            self,
            path:  PathLink,
            /, *,
            ftype: Literal['txt', 'json', 'yaml', 'csv', 'obj'] = None
    ):
        self.path  = path
        self.ftype = ftype

    def open(self, **kw) -> TextIO:
        raise NotImplementedError

    @property
    def basename(self) -> BytesOrStr:
        return os.path.basename(self.path)

    @property
    def dirname(self) -> BytesOrStr:
        return os.path.dirname(self.path)

    def dirnamel(self, level: int) -> BytesOrStr:
        """Similar to `self.dirname` and can specify the directory level."""
        return self.path.rsplit(os.sep, maxsplit=level)[0]

    @property
    def abspath(self) -> BytesOrStr:
        return os.path.abspath(self.path)

    def split(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return os.path.split(self.path)

    def splitext(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return os.path.splitext(self.path)

    @property
    def extension(self) -> BytesOrStr:
        return os.path.splitext(self.path)[1]

    def splitdrive(self) -> Tuple[BytesOrStr, BytesOrStr]:
        return os.path.splitdrive(self.path)

    def isabs(self) -> bool:
        return os.path.isabs(self.path)

    def isfile(self) -> bool:
        return os.path.isfile(self.path)

    def exists(self) -> bool:
        """Check if the file exists and return True or False. Return False for
        broken symbolic links."""
        return os.path.exists(self.path)

    def lexists(self) -> bool:
        """Check if the file exists and return True or False. Return True for
        broken symbolic links."""
        return os.path.lexists(self.path)

    def rename(self, dst: PathLink, /) -> PathLink:
        """
        Rename the file, call `os.rename` internally.

        Important Note:
        If the destination is a relative path, the parent path of the source is
        used as the parent path of the destination instead of using the current
        working directory, different from normal processing.

        For more details https://github.com/gqylpy/gqylpy-filesystem/issues/1

        @return: The destination absolute path.
        """

    def move(
            self,
            dst:           PathLink,
            /, *,
            copy_function: Callable[[PathLink, PathLink], None] = None
    ) -> PathLink:
        """
        Move the file, call `shutil.move` internally.

        The optional parameter `copy_function` will be passed to `shutil.move`
        and default value is `shutil.copy2`.

        Important Note:
        If the destination is a relative path, the parent path of the source is
        used as the parent path of the destination instead of using the current
        working directory, different from normal processing.

        For more details https://github.com/gqylpy/gqylpy-filesystem/issues/1

        @return: The destination absolute path.
        """

    def copy(
            self,
            dst:             PathLink,
            /, *,
            follow_symlinks: bool     = None
    ) -> PathLink:
        """
        Copy the file, call `shutil.copyfile` internally.

        The optional parameter `follow_symlinks` will be passed to
        `shutil.copyfile` and default value is True. If specify as False, and
        the last element of the path is a symbolic link, will modify the
        symbolic link itself instead of the file the link points to.

        Important Note:
        If the destination is a relative path, the parent path of the source is
        used as the parent path of the destination instead of using the current
        working directory, different from normal processing.

        @return: The destination absolute path.
        """

    def copyobj(self, fdst: TextIO, /) -> None:
        pass

    def truncate(self, length: int) -> None:
        os.truncate(self.path, length)

    def clear(self) -> None:
        self.truncate(0)

    def mknod(
            self,
            mode:          int           = None,
            *,
            device:        int           = None,
            dir_fd:        Optional[int] = None,
            ignore_exists: bool          = False
    ) -> None:
        """
        Create the file, call `os.mknod` internally, but if your platform is
        windows then internally call `open(self.path, 'w').close()`.

        @param mode
            Specify the access permissions of the file, could be a permission
            mask (0o600), could be a combination (0o600|stat.S_IFREG), could be
            a bitwise (33152), and default is 0o600(-rw-------).

        @param device
            Default 0, no more description. You can look up the `os.mknod`
            function.

        @param ignore_exists
            If the file already exists, call this method will raise
            `FileExistsError`. But, if this parameter is set to True then
            silently skip. Default False.

        @param dir_fd
            A file descriptor open to a directory, obtain by `os.open`, sample
            `os.open('dir/', os.O_RDONLY)`. If this parameter is specified and
            the file path is relative, the file path will then be relative to
            that directory.

        Parameters `device` and `dir_fd` may not be available on your platform,
        using them will ignored if unavailable.
        """

    def remove(self) -> None:
        os.remove(self.path)

    @property
    def stat(self) -> os.stat_result:
        return os.stat(self.path)

    @property
    def size(self) -> int:
        return os.path.getsize(self.path)

    @property
    def create_time(self) -> float:
        return os.path.getctime(self.path)

    @property
    def modify_time(self) -> float:
        return os.path.getmtime(self.path)

    @property
    def access_time(self) -> float:
        return os.path.getatime(self.path)

    def chmod(
            self,
            mode:            int,
            *,
            dir_fd:          Optional[int] = None,
            follow_symlinks: bool          = None
    ) -> None:
        """
        Change the access permissions of the file, call `os.chmod` internally.

        @param mode
            Specify the access permissions of the file, could be a permission
            mask (0o600), could be a combination (0o600|stat.S_IFREG), could be
            a bitwise (33152).

        @param dir_fd
            A file descriptor open to a directory, obtain by `os.open`, sample
            `os.open('dir/', os.O_RDONLY)`. If this parameter is specified and
            the file path is relative, the file path will then be relative to
            that directory.

        @param follow_symlinks
            Default is True. If specify as False, and the last element of the
            path is a symbolic link, will modify the symbolic link itself
            instead of the file the link points to.

        Parameters `dir_fd` and `follow_symlinks` may not be available on your
        platform, using them will raise `NotImplementedError` if unavailable.
        """

    def access(
            self,
            mode:            int,
            *,
            dir_fd:          Optional[int] = None,
            effective_ids:   bool          = None,
            follow_symlinks: bool          = None
    ) -> bool:
        """
        Test the file access permissions with the real uid/gid, call `os.access`
        internally.

        @param mode
            Test which access permissions, can be the inclusive-or(`|`) of:
                `os.R_OK`: real value is 4, whether readable.
                `os.W_OK`: real value is 2, whether writeable.
                `os.X_OK`: real value is 1, whether executable.
                `os.F_OK`: real value is 0, whether existence.

        @param dir_fd
            A file descriptor open to a directory, obtain by `os.open`, sample
            `os.open('dir/', os.O_RDONLY)`. If this parameter is specified and
            the file path is relative, the file path will then be relative to
            that directory.

        @param effective_ids
            Default False, no more description. You can look up the `os.access`
            function.

        @param follow_symlinks
            Default is True. If specify as False, and the last element of the
            path is a symbolic link, will modify the symbolic link itself
            instead of the file the link points to.

        Parameters `dir_fd`, `effective_ids` and `follow_symlinks` may not be
        available on your platform, using them will raise `NotImplementedError`
        if unavailable.
        """

    if sys.platform != 'win32':
        def chown(
                self,
                uid:             int,
                gid:             int,
                *,
                dir_fd:          Optional[int] = None,
                follow_symlinks: bool          = True
        ) -> None:
            """
            Change the file owner and owner group, call `os.chown` internally.

            @param uid
                Specify the owner id of the file, obtain by `os.getuid()`.

            @param gid
                Specify the owner group id of the file, obtain by `os.getgid()`.

            @param dir_fd
                A file descriptor open to a directory, obtain by `os.open`,
                sample `os.open('dir/', os.O_RDONLY)`. If this parameter is
                specified and the file path is relative, the file path will
                then be relative to that directory.

            @param follow_symlinks
                Default is True. If specify as False, and the last element of
                the path is a symbolic link, will modify the symbolic link
                itself instead of the file the link points to.
            """

        def chflags(self):
            raise NotImplementedError

        def chattr(self, operator: Literal['+', '-', '='], attrs: str) -> None:
            """
            Change the hidden attributes of the file, call the Unix command
            `chattr` internally.

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
                More attributes that are rarely used (or no longer used).

            Warning, do not attempt to modify hidden attributes of important
            files in your system, this may cause your system failure, unable to
            start!
            """

        def lsattr(self) -> str:
            """Return the hidden attributes of the file, call the Unix command
            `chattr` internally."""

        def exattr(self, attr: str, /) -> bool:
            """Check whether the file has a hidden attribute and return True or
            False. The usage of parameter `attr` can be seen in method `chattr`.
            """
            return attr in self.lsattr()


class _xe6_xad_x8c_xe7_x90_xaa_xe6_x80_xa1_xe7_x8e_xb2_xe8_x90_x8d_xe4_xba_x91:
    __import__(f'{__name__}.g {__name__[7:]}')
    gpack = sys.modules[__name__]
    gcode = globals()[f'g {__name__[7:]}']

    for gname in globals():
        if gname[0] != '_' and hasattr(gcode, gname):
            setattr(gpack, gname, getattr(gcode, gname))

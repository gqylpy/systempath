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
from typing import TextIO, Union, Literal, Tuple, Callable, Optional

PathLink = BytesOrStr = Union[bytes, str]


class File:
    handle: TextIO

    def __init__(
            self,
            path: PathLink,
            /, *,
            ftype: Literal['txt', 'json', 'yaml', 'csv', 'obj'] = None,
            auto_ftype: bool = False
    ):
        self.path  = path
        self.ftype = ftype

    def open(self, **kw) -> TextIO:
        if not self.handle:
            self.handle = open(self.path, **kw)
        return self.handle

    def __enter__(self) -> 'File':
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        pass

    def __del__(self) -> None:
        if self.handle:
            self.handle.close()

    @property
    def basename(self) -> BytesOrStr:
        return os.path.basename(self.path)

    @property
    def dirname(self) -> BytesOrStr:
        return os.path.dirname(self.path)

    def dirnamel(self, level: int) -> BytesOrStr:
        """Similar to `self.dirname` and can specify the directory level."""
        return self.path.rsplit(os.sep, level)[0]

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
        """Check if the `self.path` exists and return `True` or `False`. Return
        `False` for broken symbolic links."""
        return os.path.exists(self.path)

    def lexists(self) -> bool:
        """Check if the `self.path` exists and return `True` or `False`. Return
        `True` for broken symbolic links."""
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
            dst: PathLink,
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
            dst: PathLink,
            /, *,
            follow_symlinks: bool = None
    ) -> PathLink:
        """
        Copy the file, call `shutil.copyfile` internally.

        The optional parameter `follow_symlinks` will be passed to
        `shutil.copyfile` and default value is `True`.

        Important Note:
        If the destination is a relative path, the parent path of the source is
        used as the parent path of the destination instead of using the current
        working directory, different from normal processing.

        @return: The destination absolute path.
        """

    def copyobj(self, fdst: 'TextIO', /) -> None:
        with open(self.path) as fsrc:
            shutil.copyfileobj(fsrc, fdst)

    def truncate(self, length: int):
        os.truncate(self.path, length)

    def clear(self):
        os.truncate(self.path, 0)

    def mknod(
            self,
            mode:   int = None,
            device: int = None,
            *,
            dir_fd:    'Optional[int]' = None,
            ignore_err: bool           = False
    ):
        pass

    def remove(self):
        os.remove(self.path)

    @property
    def stat(self):
        return os.stat(self.path)

    @property
    def size(self):
        return os.path.getsize(self.path)

    @property
    def create_time(self):
        return os.path.getctime(self.path)

    @property
    def modify_time(self):
        return os.path.getmtime(self.path)

    @property
    def access_time(self):
        return os.path.getatime(self.path)

    def chmod(self, *a, **kw):
        raise NotImplementedError

    def chown(self, *a, **kw):
        raise NotImplementedError

    def chflags(self, *a, **kw):
        raise NotImplementedError


class _xe6_xad_x8c_xe7_x90_xaa_xe6_x80_xa1_xe7_x8e_xb2_xe8_x90_x8d_xe4_xba_x91:
    import sys

    __import__(f'{__name__}.g {__name__[7:]}')
    gpack = sys.modules[__name__]
    gcode = globals()[f'g {__name__[7:]}']

    for gname in globals():
        if gname[0] != '_' and hasattr(gcode, gname):
            setattr(gpack, gname, getattr(gcode, gname))


import os
import shutil

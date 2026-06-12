"""FTP/SFTP client adapters.

Every API request creates its own client and closes it when done, so
concurrent requests from multiple users never share connection state.
"""

from __future__ import annotations

import ftplib
import socket
import stat
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import BinaryIO, Protocol

import paramiko

CONNECT_TIMEOUT_SECONDS = 10
TRANSFER_CHUNK_SIZE = 64 * 1024
FTP_UNSUPPORTED_COMMAND_CODES = ("500", "502")


class StorageConnectError(Exception):
    """Failed to connect or authenticate against the remote server."""


class StorageOperationError(Exception):
    """A remote file operation failed."""


@dataclass(frozen=True)
class RemoteEntry:
    name: str
    is_dir: bool
    size: int
    modified_at: str


class StorageClient(Protocol):
    def list_dir(self, path: str) -> list[RemoteEntry]: ...

    def is_dir(self, path: str) -> bool: ...

    def open_download(self, path: str) -> Iterator[bytes]: ...

    def upload(self, path: str, fileobj: BinaryIO) -> None: ...

    def delete_file(self, path: str) -> None: ...

    def delete_empty_dir(self, path: str) -> None: ...

    def mkdir(self, path: str) -> None: ...

    def rename(self, old_path: str, new_path: str) -> None: ...

    def close(self) -> None: ...


def create_client(protocol: str, host: str, port: int, username: str, password: str) -> StorageClient:
    if protocol == "sftp":
        return SftpClient(host, port, username, password)
    return FtpClient(host, port, username, password)


class FtpClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.ftp = ftplib.FTP()
        self.ftp.encoding = "utf-8"
        try:
            self.ftp.connect(host, port, timeout=CONNECT_TIMEOUT_SECONDS)
            self.ftp.login(username, password)
        except ftplib.all_errors as exc:
            self.close()
            raise StorageConnectError(str(exc)) from exc

    def list_dir(self, path: str) -> list[RemoteEntry]:
        try:
            return self._list_dir_mlsd(path)
        except ftplib.error_perm as exc:
            if str(exc)[:3] not in FTP_UNSUPPORTED_COMMAND_CODES:
                raise StorageOperationError(str(exc)) from exc
        except ftplib.all_errors as exc:
            raise StorageOperationError(str(exc)) from exc
        try:
            return self._list_dir_plain(path)
        except ftplib.all_errors as exc:
            raise StorageOperationError(str(exc)) from exc

    def is_dir(self, path: str) -> bool:
        current = self.ftp.pwd()
        try:
            self.ftp.cwd(path)
            return True
        except ftplib.all_errors:
            return False
        finally:
            try:
                self.ftp.cwd(current)
            except ftplib.all_errors:
                pass

    def open_download(self, path: str) -> Iterator[bytes]:
        try:
            self.ftp.voidcmd("TYPE I")
            conn = self.ftp.transfercmd(f"RETR {path}")
        except ftplib.all_errors as exc:
            raise StorageOperationError(str(exc)) from exc

        def stream() -> Iterator[bytes]:
            try:
                while chunk := conn.recv(TRANSFER_CHUNK_SIZE):
                    yield chunk
                conn.close()
                self.ftp.voidresp()
            finally:
                conn.close()

        return stream()

    def upload(self, path: str, fileobj: BinaryIO) -> None:
        self._run(lambda: self.ftp.storbinary(f"STOR {path}", fileobj))

    def delete_file(self, path: str) -> None:
        self._run(lambda: self.ftp.delete(path))

    def delete_empty_dir(self, path: str) -> None:
        self._run(lambda: self.ftp.rmd(path))

    def mkdir(self, path: str) -> None:
        self._run(lambda: self.ftp.mkd(path))

    def rename(self, old_path: str, new_path: str) -> None:
        self._run(lambda: self.ftp.rename(old_path, new_path))

    def close(self) -> None:
        try:
            self.ftp.quit()
        except (OSError, ftplib.Error):
            try:
                self.ftp.close()
            except OSError:
                pass

    def _run(self, action) -> None:
        try:
            action()
        except ftplib.all_errors as exc:
            raise StorageOperationError(str(exc)) from exc

    def _list_dir_mlsd(self, path: str) -> list[RemoteEntry]:
        entries = []
        for name, facts in self.ftp.mlsd(path):
            entry_type = facts.get("type", "file")
            if name in (".", "..") or entry_type in ("cdir", "pdir"):
                continue
            entries.append(
                RemoteEntry(
                    name=name,
                    is_dir=entry_type == "dir",
                    size=_safe_int(facts.get("size", "")),
                    modified_at=_ftp_modify_to_iso(facts.get("modify", "")),
                )
            )
        return entries

    def _list_dir_plain(self, path: str) -> list[RemoteEntry]:
        lines: list[str] = []
        self.ftp.retrlines(f"LIST {path}", lines.append)
        entries = []
        for line in lines:
            entry = _parse_list_line(line)
            if entry is not None:
                entries.append(entry)
        return entries


class SftpClient:
    def __init__(self, host: str, port: int, username: str, password: str):
        self.transport: paramiko.Transport | None = None
        try:
            sock = socket.create_connection((host, port), timeout=CONNECT_TIMEOUT_SECONDS)
            self.transport = paramiko.Transport(sock)
            self.transport.banner_timeout = CONNECT_TIMEOUT_SECONDS
            self.transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(self.transport)
            if sftp is None:
                raise StorageConnectError("SFTP channel unavailable")
            self.sftp = sftp
            channel = self.sftp.get_channel()
            if channel is not None:
                channel.settimeout(CONNECT_TIMEOUT_SECONDS * 6)
        except (OSError, EOFError, paramiko.SSHException) as exc:
            self.close()
            raise StorageConnectError(str(exc)) from exc

    def list_dir(self, path: str) -> list[RemoteEntry]:
        attrs = self._run(lambda: self.sftp.listdir_attr(path))
        entries = []
        for attr in attrs:
            modified = ""
            if attr.st_mtime:
                modified = datetime.fromtimestamp(attr.st_mtime, tz=timezone.utc).isoformat()
            entries.append(
                RemoteEntry(
                    name=attr.filename,
                    is_dir=stat.S_ISDIR(attr.st_mode or 0),
                    size=int(attr.st_size or 0),
                    modified_at=modified,
                )
            )
        return entries

    def is_dir(self, path: str) -> bool:
        attr = self._run(lambda: self.sftp.stat(path))
        return stat.S_ISDIR(attr.st_mode or 0)

    def open_download(self, path: str) -> Iterator[bytes]:
        handle = self._run(lambda: self.sftp.open(path, "rb"))

        def stream() -> Iterator[bytes]:
            with handle:
                while chunk := handle.read(TRANSFER_CHUNK_SIZE):
                    yield chunk

        return stream()

    def upload(self, path: str, fileobj: BinaryIO) -> None:
        self._run(lambda: self.sftp.putfo(fileobj, path))

    def delete_file(self, path: str) -> None:
        self._run(lambda: self.sftp.remove(path))

    def delete_empty_dir(self, path: str) -> None:
        self._run(lambda: self.sftp.rmdir(path))

    def mkdir(self, path: str) -> None:
        self._run(lambda: self.sftp.mkdir(path))

    def rename(self, old_path: str, new_path: str) -> None:
        self._run(lambda: self.sftp.rename(old_path, new_path))

    def close(self) -> None:
        if self.transport is not None:
            try:
                self.transport.close()
            except (OSError, EOFError, paramiko.SSHException):
                pass

    def _run(self, action):
        try:
            return action()
        except (OSError, EOFError, paramiko.SSHException) as exc:
            raise StorageOperationError(str(exc)) from exc


def _safe_int(value: str) -> int:
    try:
        return int(value)
    except ValueError:
        return 0


def _ftp_modify_to_iso(value: str) -> str:
    digits = value.strip()[:14]
    if len(digits) < 14 or not digits.isdigit():
        return ""
    try:
        return datetime.strptime(digits, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc).isoformat()
    except ValueError:
        return ""


def _parse_list_line(line: str) -> RemoteEntry | None:
    text = line.rstrip()
    if not text or text.startswith("total "):
        return None
    if text[0] in "dl-" and len(text) >= 10:
        parts = text.split(maxsplit=8)
        if len(parts) < 9:
            return None
        name = parts[8]
        if text[0] == "l" and " -> " in name:
            name = name.split(" -> ", 1)[0]
        if name in (".", ".."):
            return None
        return RemoteEntry(name=name, is_dir=text[0] == "d", size=_safe_int(parts[4]), modified_at="")
    parts = text.split(maxsplit=3)
    if len(parts) == 4 and parts[0].count("-") == 2:
        is_dir = parts[2] == "<DIR>"
        return RemoteEntry(name=parts[3], is_dir=is_dir, size=0 if is_dir else _safe_int(parts[2]), modified_at="")
    return None

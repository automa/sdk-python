from __future__ import annotations

import json
import subprocess
import tarfile
from asyncio import to_thread
from os import makedirs, remove
from os.path import join
from pathlib import Path
from shutil import rmtree
from typing import NotRequired, TypedDict

from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import RequestOptions

__all__ = [
    "CodeResource",
    "AsyncCodeResource",
    "CodeFolder",
    "CodeCleanupParams",
    "CodeDownloadParams",
    "CodeProposeParams",
]


# TODO: Use programmatic git instead of git command
def get_diff(path: str) -> str:
    """Get the diff for the given git repository path."""
    result = subprocess.run(
        ["git", "diff"],
        cwd=path,
        capture_output=True,
        text=True,
        check=True,
    )

    return result.stdout


class CodeFolder:
    def __init__(self, path: str):
        self.path = path

    def add(self, paths: str | list[str]) -> None:
        """Add new files to git repository"""
        paths = paths if isinstance(paths, list) else [paths]
        paths = [join(self.path, p) for p in paths if p]

        subprocess.run(
            ["git", "add", "-N", *paths],
            cwd=self.path,
            check=True,
        )

    def add_all(self) -> None:
        """Add all files to git repository"""
        subprocess.run(
            ["git", "add", "-N", "."],
            cwd=self.path,
            check=True,
        )


class BaseCodeResource:
    def _path(self, task: Task) -> str:
        return f"/tmp/automa/tasks/{task['id']}"

    def _read_token(self, folder: str) -> str | None:
        token = None

        try:
            with open(
                f"{folder}/.git/automa_proposal_token", "r", encoding="utf8"
            ) as f:
                token = f.read().strip()
        except FileNotFoundError:
            pass

        return token

    def _read_base_commit(self, folder: str) -> str | None:
        base_commit = None

        try:
            with open(
                f"{folder}/.git/automa_proposal_base_commit", "r", encoding="utf8"
            ) as f:
                base_commit = f.read().strip()
        except FileNotFoundError:
            pass

        return base_commit

    def _clone_code(self, folder: str, url: str) -> None:
        path = Path(folder)

        rmtree(folder, ignore_errors=True)
        path.mkdir(parents=True, exist_ok=True)

        subprocess.run(
            ["git", "clone", "--depth=1", url, "."],
            cwd=path,
            check=True,
        )

        # Note down the base commit
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True,
        )

        self._write_base_commit(folder, result.stdout.strip())

    def _extract_download(self, folder: str) -> None:
        rmtree(folder, ignore_errors=True)
        Path(folder).mkdir(parents=True, exist_ok=True)

        with tarfile.open(f"{folder}.tar.gz", "r:gz") as tar:
            tar.extractall(path=folder)

    def _write_token(self, folder: str, token: str) -> None:
        # Save the proposal token for later use
        with open(f"{folder}/.git/automa_proposal_token", "w", encoding="utf8") as f:
            f.write(token)

    def _write_base_commit(self, folder: str, base_commit: str) -> None:
        # Save the base commit for later use
        with open(
            f"{folder}/.git/automa_proposal_base_commit", "w", encoding="utf8"
        ) as f:
            f.write(base_commit)


class CodeResource(SyncAPIResource, BaseCodeResource):
    def cleanup(self, body: CodeCleanupParams) -> None:
        folder = self._path(body["task"])

        rmtree(folder, ignore_errors=True)

        try:
            remove(f"{folder}.tar.gz")
        except FileNotFoundError:
            pass

    def download(
        self, body: CodeDownloadParams, *, options: RequestOptions = {}
    ) -> CodeFolder:
        token = None
        path = self._path(body["task"])
        archive_path = f"{path}.tar.gz"

        with self._client.stream(
            "post",
            "/code/download",
            options={
                **options,
                "json": body,
                "headers": {
                    **options.get("headers", {}),
                },
            },
        ) as response:
            token = response.headers.get("x-automa-proposal-token")
            content_type = response.headers.get("Content-Type", "")

            if content_type.startswith("application/json"):
                content = b"".join(response.iter_bytes())

                json_data = json.loads(content.decode("utf-8"))

                self._clone_code(path, json_data["url"])
            elif content_type.startswith("application/gzip"):
                rmtree(path, ignore_errors=True)
                makedirs(path, exist_ok=True)

                with open(archive_path, "wb") as archive:
                    for chunk in response.iter_bytes(chunk_size=8192):
                        archive.write(chunk)

                self._extract_download(path)
            else:
                raise ValueError(
                    f"Unexpected Content-Type: {content_type} while downloading code."
                )

        # Save the proposal token for later use
        self._write_token(path, token)

        return CodeFolder(path)

    def propose(self, body: CodeProposeParams, *, options: RequestOptions = {}):
        path = self._path(body["task"])
        token = self._read_token(path)
        base_commit = self._read_base_commit(path)

        if not token:
            raise ValueError("Failed to read the stored proposal token")

        diff = get_diff(path)

        return self._client.post(
            "/code/propose",
            body={
                **body,
                "proposal": {
                    **body.get("proposal", {}),
                    "token": token,
                    "diff": diff,
                    **({"base_commit": base_commit} if base_commit else {}),
                },
            },
            options=options,
        )


class AsyncCodeResource(AsyncAPIResource, BaseCodeResource):
    async def cleanup(self, body: CodeCleanupParams) -> None:
        folder = self._path(body["task"])

        await to_thread(rmtree, folder, ignore_errors=True)

        try:
            await to_thread(remove, f"{folder}.tar.gz")
        except FileNotFoundError:
            pass

    async def download(
        self, body: CodeDownloadParams, *, options: RequestOptions = {}
    ) -> CodeFolder:
        token = None
        path = self._path(body["task"])
        archive_path = f"{path}.tar.gz"

        async with self._client.stream(
            "post",
            "/code/download",
            options={
                **options,
                "json": body,
                "headers": {
                    **options.get("headers", {}),
                },
            },
        ) as response:
            token = response.headers.get("x-automa-proposal-token")
            content_type = response.headers.get("Content-Type", "")

            if content_type.startswith("application/json"):
                content = b""

                async for chunk in response.aiter_bytes():
                    content += chunk

                json_data = json.loads(content.decode("utf-8"))

                await to_thread(self._clone_code, path, json_data["url"])
            elif content_type.startswith("application/gzip"):
                await to_thread(rmtree, path, ignore_errors=True)
                await to_thread(makedirs, path, exist_ok=True)

                with open(archive_path, "wb") as archive:
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        await to_thread(archive.write, chunk)

                await to_thread(self._extract_download, path)
            else:
                raise ValueError(
                    f"Unexpected Content-Type: {content_type} while downloading code."
                )

        # Save the proposal token for later use
        await to_thread(self._write_token, path, token)

        return CodeFolder(path)

    async def propose(self, body: CodeProposeParams, *, options: RequestOptions = {}):
        path = self._path(body["task"])
        token = await to_thread(self._read_token, path)
        base_commit = await to_thread(self._read_base_commit, path)

        if not token:
            raise ValueError("Failed to read the stored proposal token")

        diff = await to_thread(get_diff, path)

        return await self._client.post(
            "/code/propose",
            body={
                **body,
                "proposal": {
                    **body.get("proposal", {}),
                    "token": token,
                    "diff": diff,
                    **({"base_commit": base_commit} if base_commit else {}),
                },
            },
            options=options,
        )


class Task(TypedDict):
    id: int


class TaskWithToken(Task):
    token: str


class CodeCleanupParams(TypedDict):
    task: Task


class CodeDownloadParams(TypedDict):
    task: TaskWithToken


class CodeProposeParams(CodeDownloadParams):
    proposal: NotRequired[Proposal]
    metadata: NotRequired[Metadata]

    class Proposal(TypedDict):
        title: NotRequired[str]
        body: NotRequired[str]

    # TODO: Add `extra_items=Any` (py 3.15)
    class Metadata(TypedDict):
        cost: NotRequired[float]

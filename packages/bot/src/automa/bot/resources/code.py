from __future__ import annotations

import tarfile
from asyncio import to_thread
from os import makedirs, remove
from pathlib import Path
from shutil import rmtree
from typing import NotRequired, TypedDict

from git import Repo

from .._resource import AsyncAPIResource, SyncAPIResource
from .._types import RequestOptions
from .shared.task import Task, TaskWithToken

__all__ = [
    "CodeResource",
    "AsyncCodeResource",
]


def get_diff(folder: str) -> str:
    repo = Repo(folder)
    return repo.git.diff(strip_newline_in_stdout=False)


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

    def _extract_download(self, folder: str) -> None:
        rmtree(folder, ignore_errors=True)
        Path(folder).mkdir(parents=True, exist_ok=True)

        with tarfile.open(f"{folder}.tar.gz", "r:gz") as tar:
            tar.extractall(path=folder)

    def _write_token(self, folder: str, token: str) -> None:
        # Save the proposal token for later use
        with open(f"{folder}/.git/automa_proposal_token", "w", encoding="utf8") as f:
            f.write(token)


class CodeResource(SyncAPIResource, BaseCodeResource):
    def cleanup(self, body: CodeCleanupParams) -> None:
        folder = self._path(body["task"])

        rmtree(folder, ignore_errors=True)
        remove(f"{folder}.tar.gz")

    def download(
        self, body: CodeDownloadParams, *, options: RequestOptions = {}
    ) -> str:
        token = None
        folder = self._path(body["task"])
        archive_path = f"{folder}.tar.gz"

        with self._client.stream(
            "post",
            "/code/download",
            options={
                **options,
                "json": body,
                "headers": {
                    **options.get("headers", {}),
                    "Accept": "application/gzip",
                },
            },
        ) as response:
            token = response.headers["x-automa-proposal-token"]

            rmtree(folder, ignore_errors=True)
            makedirs(folder, exist_ok=True)

            with open(archive_path, "wb") as archive:
                for chunk in response.iter_bytes(chunk_size=8192):
                    archive.write(chunk)

        self._extract_download(folder)

        # Save the proposal token for later use
        self._write_token(folder, token)

        return folder

    def propose(self, body: CodeProposeParams, *, options: RequestOptions = {}):
        folder = self._path(body["task"])
        token = self._read_token(folder)

        if not token:
            raise ValueError("Failed to read the stored proposal token")

        diff = get_diff(folder)

        return self._client.post(
            "/code/propose",
            body={
                **body,
                "proposal": {
                    **body.get("proposal", {}),
                    "token": token,
                    "diff": diff,
                },
            },
            options=options,
        )


class AsyncCodeResource(AsyncAPIResource, BaseCodeResource):
    async def cleanup(self, body: CodeCleanupParams) -> None:
        folder = self._path(body["task"])

        await to_thread(rmtree, folder, ignore_errors=True)
        await to_thread(remove, f"{folder}.tar.gz")

    async def download(
        self, body: CodeDownloadParams, *, options: RequestOptions = {}
    ) -> str:
        token = None
        folder = self._path(body["task"])
        archive_path = f"{folder}.tar.gz"

        async with self._client.stream(
            "post",
            "/code/download",
            options={
                **options,
                "json": body,
                "headers": {
                    **options.get("headers", {}),
                    "Accept": "application/gzip",
                },
            },
        ) as response:
            token = response.headers["x-automa-proposal-token"]

            await to_thread(rmtree, folder, ignore_errors=True)
            await to_thread(makedirs, folder, exist_ok=True)

            with open(archive_path, "wb") as archive:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    await to_thread(archive.write, chunk)

        await to_thread(self._extract_download, folder)

        # Save the proposal token for later use
        await to_thread(self._write_token, folder, token)

        return folder

    async def propose(self, body: CodeProposeParams, *, options: RequestOptions = {}):
        folder = self._path(body["task"])
        token = await to_thread(self._read_token, folder)

        if not token:
            raise ValueError("Failed to read the stored proposal token")

        diff = await to_thread(get_diff, folder)

        return await self._client.post(
            "/code/propose",
            body={
                **body,
                "proposal": {
                    **body.get("proposal", {}),
                    "token": token,
                    "diff": diff,
                },
            },
            options=options,
        )


class CodeCleanupParams(TypedDict):
    task: Task


class CodeDownloadParams(TypedDict):
    task: TaskWithToken


class CodeProposeParams(CodeDownloadParams):
    proposal: NotRequired[Proposal]

    class Proposal(TypedDict, total=False):
        message: str

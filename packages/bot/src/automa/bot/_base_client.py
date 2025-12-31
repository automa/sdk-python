from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager, contextmanager
from types import TracebackType
from typing import (
    Any,
    AsyncIterator,
    Generic,
    Iterator,
    TypeVar,
    Union,
    cast,
)

from httpx import URL, AsyncClient, Client, Response
from httpx._types import HeaderTypes

from ._types import RequestOptions

_T = TypeVar("_T")

_HttpxClientT = TypeVar("_HttpxClientT", bound=Union[Client, AsyncClient])


class BaseClient(Generic[_HttpxClientT]):
    _client: _HttpxClientT
    _base_url: URL

    def __init__(
        self,
        *,
        base_url: str | URL,
    ) -> None:
        self.base_url = base_url

    def _enforce_trailing_slash(self, url: URL) -> URL:
        if url.raw_path.endswith(b"/"):
            return url
        return url.copy_with(raw_path=url.raw_path + b"/")

    @property
    def base_url(self) -> URL:
        return self._base_url

    @base_url.setter
    def base_url(self, url: str | URL) -> None:
        self._base_url = self._enforce_trailing_slash(
            url if isinstance(url, URL) else URL(url)
        )

    @property
    def default_headers(self) -> HeaderTypes:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }


class SyncHttpxClientWrapper(Client):
    def __del__(self) -> None:
        if self.is_closed:
            return

        try:
            self.close()
        except Exception:
            pass


class SyncAPIClient(BaseClient[Client]):
    _client: Client

    def __init__(
        self,
        *,
        base_url: str | URL,
    ) -> None:
        super().__init__(
            base_url=base_url,
        )
        self._client = SyncHttpxClientWrapper(
            base_url=base_url,
        )

    def is_closed(self) -> bool:
        return self._client.is_closed

    def close(self) -> None:
        """Close the underlying HTTPX client.

        The client will *not* be usable after this.
        """
        # If an error is thrown while constructing a client, self._client
        # may not be present
        if hasattr(self, "_client"):
            self._client.close()

    def __enter__(self: _T) -> _T:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()

    def get(
        self,
        path: str,
        *,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> Response:
        return self.method("get", path, options=options)

    def post(
        self,
        path: str,
        *,
        body: Any | None = None,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> Response:
        return self.method(
            "post",
            path,
            options={
                **options,
                "json": body,
            },
        )

    def method(
        self,
        method: str,
        path: str,
        *,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> Response:
        options["headers"] = {**self.default_headers, **options.get("headers", {})}

        response = self._client.request(method, path, **options)

        if response.is_error:
            data = response.json()
            raise Exception(data.get("message") or data.get("error"))

        return response

    @contextmanager
    def stream(
        self,
        method: str,
        path: str,
        *,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> Iterator[Response]:
        options["headers"] = {**self.default_headers, **options.get("headers", {})}

        with self._client.stream(method, path, **options) as response:
            if response.is_error:
                response.read()
                data = response.json()
                raise Exception(data.get("message") or data.get("error"))

            yield response


class AsyncHttpxClientWrapper(AsyncClient):
    def __del__(self) -> None:
        if self.is_closed:
            return

        try:
            asyncio.get_running_loop().create_task(self.aclose())
        except Exception:
            pass


class AsyncAPIClient(BaseClient[AsyncClient]):
    _client: AsyncClient

    def __init__(
        self,
        *,
        base_url: str | URL,
    ) -> None:
        super().__init__(
            base_url=base_url,
        )
        self._client = AsyncHttpxClientWrapper(
            base_url=base_url,
        )

    def is_closed(self) -> bool:
        return self._client.is_closed

    async def close(self) -> None:
        """Close the underlying HTTPX client.

        The client will *not* be usable after this.
        """
        await self._client.aclose()

    async def __aenter__(self: _T) -> _T:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self.close()

    async def get(
        self,
        path: str,
        *,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> Response:
        return await self.method("get", path, options=options)

    async def post(
        self,
        path: str,
        *,
        body: Any | None = None,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> Response:
        return await self.method(
            "post",
            path,
            options={
                **options,
                "json": body,
            },
        )

    async def method(
        self,
        method: str,
        path: str,
        *,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> Response:
        options["headers"] = {**self.default_headers, **options.get("headers", {})}

        response = await self._client.request(method, path, **options)

        if response.is_error:
            data = response.json()
            raise Exception(data.get("message") or data.get("error"))

        return response

    @asynccontextmanager
    async def stream(
        self,
        method: str,
        path: str,
        *,
        options: RequestOptions = cast(RequestOptions, {}),
    ) -> AsyncIterator[Response]:
        options["headers"] = {**self.default_headers, **options.get("headers", {})}

        async with self._client.stream(method, path, **options) as response:
            if response.is_error:
                await response.aread()
                data = response.json()
                raise Exception(data.get("message") or data.get("error"))

            yield response

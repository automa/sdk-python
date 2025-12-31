from __future__ import annotations

import os

from httpx import URL
from httpx._types import HeaderTypes
from typing_extensions import override

from ._base_client import (
    AsyncAPIClient,
    SyncAPIClient,
)
from .resources import code

__all__ = [
    "Automa",
    "AsyncAutoma",
]


class Automa(SyncAPIClient):
    _default_headers: HeaderTypes

    code: code.CodeResource

    def __init__(
        self,
        *,
        base_url: str | URL | None = None,
        default_headers: HeaderTypes | None = None,
    ) -> None:
        """Construct a new synchronous Automa client instance."""
        if base_url is None:
            base_url = os.environ.get("AUTOMA_BASE_URL")
        if base_url is None:
            base_url = "https://api.automa.app"

        super().__init__(
            base_url=base_url,
        )

        self._default_headers = default_headers or {}

        self.code = code.CodeResource(self)

    @property
    @override
    def default_headers(self) -> dict[str, str]:
        return {
            **super().default_headers,
            **self._default_headers,
        }


class AsyncAutoma(AsyncAPIClient):
    _default_headers: HeaderTypes

    code: code.AsyncCodeResource

    def __init__(
        self,
        *,
        base_url: str | URL | None = None,
        default_headers: HeaderTypes | None = None,
    ) -> None:
        """Construct a new async AsyncAutoma client instance."""
        if base_url is None:
            base_url = os.environ.get("AUTOMA_BASE_URL")
        if base_url is None:
            base_url = "https://api.automa.app"

        super().__init__(
            base_url=base_url,
        )

        self._default_headers = default_headers or {}

        self.code = code.AsyncCodeResource(self)

    @property
    @override
    def default_headers(self) -> HeaderTypes:
        return {
            **super().default_headers,
            **self._default_headers,
        }

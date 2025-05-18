import tarfile
from os import listdir, makedirs, path, remove
from pathlib import Path
from shutil import rmtree
from subprocess import run
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.automa.bot._client import AsyncAutoma, Automa
from src.automa.bot.resources.code import AsyncCodeResource, CodeResource

folder = "/tmp/automa/tasks/28"
proposal_token_file = f"{folder}/.git/automa_proposal_token"


@pytest.fixture
def code_resource():
    rmtree(path.dirname(folder), ignore_errors=True)

    client_mock = MagicMock()
    client = Automa()

    client._client = client_mock

    yield CodeResource(client=client)

    rmtree(path.dirname(folder), ignore_errors=True)


@pytest.fixture
def async_code_resource():
    rmtree(path.dirname(folder), ignore_errors=True)

    client_mock = MagicMock()
    client = AsyncAutoma()

    client._client = client_mock

    yield AsyncCodeResource(client=client)

    rmtree(path.dirname(folder), ignore_errors=True)


@pytest.fixture
def fixture_tarfile():
    tests_folder = Path(__file__).parent.parent
    fixture = tests_folder / "fixtures" / "download"
    tarfile_path = tests_folder / "fixture.tar.gz"

    run(["git", "init"], cwd=fixture, capture_output=True)
    run(["git", "add", "."], cwd=fixture, capture_output=True)
    run(["git", "config", "user.name", "Tmp"], cwd=fixture, capture_output=True)
    run(
        ["git", "config", "user.email", "tmp@tmp.com"], cwd=fixture, capture_output=True
    )
    run(["git", "commit", "-m", "Initial commit"], cwd=fixture, capture_output=True)

    with tarfile.open(tarfile_path, "w:gz") as tar:
        for subpath in listdir(fixture):
            tar.add(fixture / subpath, arcname=subpath)

    yield tarfile_path

    remove(tarfile_path)
    rmtree(fixture / ".git", ignore_errors=True)


def test_cleanup(code_resource):
    makedirs(folder, exist_ok=True)
    with open(f"{folder}.tar.gz", "w") as f:
        f.write("ghijkl")

    assert path.exists(folder)
    assert path.exists(f"{folder}.tar.gz")

    # Call cleanup
    code_resource.cleanup({"task": {"id": 28}})

    assert not path.exists(folder)
    assert not path.exists(f"{folder}.tar.gz")


@pytest.mark.asyncio
async def test_cleanup_async(async_code_resource):
    makedirs(folder, exist_ok=True)
    with open(f"{folder}.tar.gz", "w") as f:
        f.write("ghijkl")

    assert path.exists(folder)
    assert path.exists(f"{folder}.tar.gz")

    # Call cleanup
    await async_code_resource.cleanup({"task": {"id": 28}})

    assert not path.exists(folder)
    assert not path.exists(f"{folder}.tar.gz")


def test_download_invalid_token(code_resource):
    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 403
    response_mock.is_error = True
    response_mock.json.return_value = {
        "message": "Task is older than 7 days and thus cannot be worked upon anymore"
    }

    code_resource._client._client.stream.return_value.__enter__.return_value = (
        response_mock
    )

    # Call download
    with pytest.raises(
        Exception,
        match="Task is older than 7 days and thus cannot be worked upon anymore",
    ):
        code_resource.download({"task": {"id": 28, "token": "invalid"}})

    # Hits the API
    code_resource._client._client.stream.assert_called_once_with(
        "post",
        "/code/download",
        json={"task": {"id": 28, "token": "invalid"}},
        headers={
            "Accept": "application/gzip",
            "Content-Type": "application/json",
        },
    )

    # Does not download code
    assert not path.exists(folder)


@pytest.mark.asyncio
async def test_download_async_invalid_token(async_code_resource):
    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 403
    response_mock.is_error = True
    response_mock.aread = AsyncMock()
    response_mock.json.return_value = {
        "message": "Task is older than 7 days and thus cannot be worked upon anymore"
    }

    async_code_resource._client._client.stream.return_value.__aenter__.return_value = (
        response_mock
    )

    # Call download
    with pytest.raises(
        Exception,
        match="Task is older than 7 days and thus cannot be worked upon anymore",
    ):
        await async_code_resource.download({"task": {"id": 28, "token": "invalid"}})

    # Hits the API
    async_code_resource._client._client.stream.assert_called_once_with(
        "post",
        "/code/download",
        json={"task": {"id": 28, "token": "invalid"}},
        headers={
            "Accept": "application/gzip",
            "Content-Type": "application/json",
        },
    )

    # Does not download code
    assert not path.exists(folder)


def test_download(fixture_tarfile, code_resource):
    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.is_error = False
    response_mock.headers = {"x-automa-proposal-token": "ghijkl"}
    with open(fixture_tarfile, "rb") as f:
        response_mock.iter_bytes.return_value = iter([f.read()])

    code_resource._client._client.stream.return_value.__enter__.return_value = (
        response_mock
    )

    # Call download
    created_folder = code_resource.download({"task": {"id": 28, "token": "abcdef"}})

    # Returns path to downloaded code
    assert created_folder == folder

    # Hits the API
    code_resource._client._client.stream.assert_called_once_with(
        "post",
        "/code/download",
        json={"task": {"id": 28, "token": "abcdef"}},
        headers={
            "Accept": "application/gzip",
            "Content-Type": "application/json",
        },
    )

    # Downloads the code
    assert path.exists(folder)
    assert sorted(listdir(folder)) == [
        ".git",
        "README.md",
    ]

    # Saves proposal token
    with open(proposal_token_file, "r") as f:
        assert f.read() == "ghijkl"


@pytest.mark.asyncio
async def test_download_async(fixture_tarfile, async_code_resource):
    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 200
    response_mock.is_error = False
    response_mock.headers = {"x-automa-proposal-token": "ghijkl"}

    with open(fixture_tarfile, "rb") as f:
        response_byte_reader = AsyncMock()
        response_byte_reader.__aiter__.return_value = iter([f.read()])
        response_mock.aiter_bytes.return_value = response_byte_reader

    async_code_resource._client._client.stream.return_value.__aenter__.return_value = (
        response_mock
    )

    # Call download
    created_folder = await async_code_resource.download(
        {"task": {"id": 28, "token": "abcdef"}}
    )

    # Returns path to downloaded code
    assert created_folder == folder

    # Hits the API
    async_code_resource._client._client.stream.assert_called_once_with(
        "post",
        "/code/download",
        json={"task": {"id": 28, "token": "abcdef"}},
        headers={
            "Accept": "application/gzip",
            "Content-Type": "application/json",
        },
    )

    # Downloads the code
    assert path.exists(folder)
    assert sorted(listdir(folder)) == [
        ".git",
        "README.md",
    ]

    # Saves proposal token
    with open(proposal_token_file, "r") as f:
        assert f.read() == "ghijkl"


def test_propose_no_token(fixture_tarfile, code_resource):
    test_download(fixture_tarfile, code_resource)

    remove(proposal_token_file)

    with pytest.raises(Exception, match="Failed to read the stored proposal token"):
        code_resource.propose({"task": {"id": 28, "token": "abcdef"}})

    # Does not hit the API
    code_resource._client._client.request.assert_not_called()


@pytest.mark.asyncio
async def test_propose_async_no_token(fixture_tarfile, async_code_resource):
    await test_download_async(fixture_tarfile, async_code_resource)

    remove(proposal_token_file)

    with pytest.raises(Exception, match="Failed to read the stored proposal token"):
        await async_code_resource.propose({"task": {"id": 28, "token": "abcdef"}})

    # Does not hit the API
    async_code_resource._client._client.request.assert_not_called()


def test_propose_invalid_token(fixture_tarfile, code_resource):
    test_download(fixture_tarfile, code_resource)

    with open(f"{folder}/README.md", "w") as f:
        f.write("Content\n")

    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 403
    response_mock.is_error = True
    response_mock.json.return_value = {"message": "Wrong proposal token provided"}

    code_resource._client._client.request.return_value = response_mock

    with pytest.raises(Exception, match="Wrong proposal token provided"):
        code_resource.propose({"task": {"id": 28, "token": "abcdef"}})

    # Hits the API
    code_resource._client._client.request.assert_called_once_with(
        "post",
        "/code/propose",
        json={
            "task": {"id": 28, "token": "abcdef"},
            "proposal": {
                "token": "ghijkl",
                "diff": "diff --git a/README.md b/README.md\nindex e69de29..39c9f36 100644\n--- a/README.md\n+++ b/README.md\n@@ -0,0 +1 @@\n+Content\n",
            },
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )


@pytest.mark.asyncio
async def test_propose_async_invalid_token(fixture_tarfile, async_code_resource):
    await test_download_async(fixture_tarfile, async_code_resource)

    with open(f"{folder}/README.md", "w") as f:
        f.write("Content\n")

    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 403
    response_mock.is_error = True
    response_mock.json.return_value = {"message": "Wrong proposal token provided"}

    async_code_resource._client._client.request = AsyncMock(return_value=response_mock)

    with pytest.raises(Exception, match="Wrong proposal token provided"):
        await async_code_resource.propose({"task": {"id": 28, "token": "abcdef"}})

    # Hits the API
    async_code_resource._client._client.request.assert_called_once_with(
        "post",
        "/code/propose",
        json={
            "task": {"id": 28, "token": "abcdef"},
            "proposal": {
                "token": "ghijkl",
                "diff": "diff --git a/README.md b/README.md\nindex e69de29..39c9f36 100644\n--- a/README.md\n+++ b/README.md\n@@ -0,0 +1 @@\n+Content\n",
            },
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )


def test_propose(fixture_tarfile, code_resource):
    test_download(fixture_tarfile, code_resource)

    with open(f"{folder}/README.md", "w") as f:
        f.write("Content\n")

    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 204
    response_mock.is_error = False

    code_resource._client._client.request.return_value = response_mock

    code_resource.propose({"task": {"id": 28, "token": "abcdef"}})

    # Hits the API
    code_resource._client._client.request.assert_called_once_with(
        "post",
        "/code/propose",
        json={
            "task": {"id": 28, "token": "abcdef"},
            "proposal": {
                "token": "ghijkl",
                "diff": "diff --git a/README.md b/README.md\nindex e69de29..39c9f36 100644\n--- a/README.md\n+++ b/README.md\n@@ -0,0 +1 @@\n+Content\n",
            },
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )


@pytest.mark.asyncio
async def test_propose_async(fixture_tarfile, async_code_resource):
    await test_download_async(fixture_tarfile, async_code_resource)

    with open(f"{folder}/README.md", "w") as f:
        f.write("Content\n")

    # Mock client response
    response_mock = MagicMock()
    response_mock.status_code = 204
    response_mock.is_error = False

    async_code_resource._client._client.request = AsyncMock(return_value=response_mock)

    await async_code_resource.propose({"task": {"id": 28, "token": "abcdef"}})

    # Hits the API
    async_code_resource._client._client.request.assert_called_once_with(
        "post",
        "/code/propose",
        json={
            "task": {"id": 28, "token": "abcdef"},
            "proposal": {
                "token": "ghijkl",
                "diff": "diff --git a/README.md b/README.md\nindex e69de29..39c9f36 100644\n--- a/README.md\n+++ b/README.md\n@@ -0,0 +1 @@\n+Content\n",
            },
        },
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
        },
    )

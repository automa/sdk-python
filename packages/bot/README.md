# automa-bot

Bot SDK for Automa.

Please read more about Automa [Bots](https://docs.automa.app/bots) and their [development](https://docs.automa.app/bot-development) in our documentation.

1. [Installation](#installation)
2. [Usage](#usage)
3. [Webhook signatures](#webhook-signatures)
4. [Testing](#testing)
5. [Reference](#reference)

## Installation

```sh
# Using pip
pip install automa-bot

# Using uv
uv add automa-bot
```

## Usage

```python
from automa import Automa

client = Automa()

def main():
  # Download code for a task
  folder = client.code.download({
    "task": {
      "id": 10,
      "token": '3ee12f8ca60132c087c6303efb46c3b5',
    },
  })

  # Change code in the folder ...

  # Propose the changed code
  client.code.propose({
    "task": { "id": 10 },
  })

  # Remove the downloaded code folder
  client.code.cleanup({
    "task": { "id": 10 },
  })

main()
```

### Asynchronous

Simply import `AsyncAutoma` instead of `Automa` and use `await` with each method call:

```python
import asyncio
from automa import AsyncAutoma

client = AsyncAutoma()

async def main() -> None:
  # Download code for a task
  folder = await client.code.download({
    "task": {
      "id": 10,
      "token": '3ee12f8ca60132c087c6303efb46c3b5',
    },
  })

  # Change code in the folder ...

  # Propose the changed code
  await client.code.propose({
    "task": { "id": 10 },
  })

  # Remove the downloaded code folder
  await client.code.cleanup({
    "task": { "id": 10 },
  })

asyncio.run(main())
```

Functionality between the synchronous and asynchronous clients is otherwise identical.

### Managing client resource

By default the library closes underlying HTTP connections whenever the client is [garbage collected](https://docs.python.org/3/reference/datamodel.html#object.__del__). You can manually close the client using the `.close()` method if desired, or with a context manager that closes when exiting.

```py
from automa import Automa

with Automa() as client:
  # make requests here
  ...

# HTTP client is now closed
```

## Webhook signatures

To verify webhook signatures, you can use the `verify_webhook` helper provided by the SDK.

```python
import os
from automa.bot.webhook import verify_webhook

payload = (await request.body()).decode("utf-8") # The body of the webhook request
signature = request.headers.get('webhook-signature') # The signature header from the request

is_valid = verify_webhook(
  os.environ['AUTOMA_WEBHOOK_SECRET'],
  signature,
  payload
)
```

## Testing

When writing tests for your bot, you can mock the client methods to simulate the behavior of the SDK without making actual network requests.

```python
from automa.bot import CodeFolder

fixture_code = CodeFolder("." / "fixtures" / "code")

@patch("automa.bot.AsyncCodeResource.cleanup")
@patch("automa.bot.AsyncCodeResource.propose")
@patch("automa.bot.AsyncCodeResource.download", return_value=fixture_code)
def test(download_mock, propose_mock, cleanup_mock):
  pass
```

### Webhook signatures in tests

When testing webhook handling, you may want to simulate valid webhook requests. The SDK provides `generate_webhook_signature` helper to generate valid signatures for your test payloads.

```python
import os
from automa.bot.webhook import generate_webhook_signature

payload = '{}' # Example payload

signature = generate_webhook_signature(
  os.environ['AUTOMA_WEBHOOK_SECRET'],
  payload
)

# Use this signature in your tests to simulate a valid webhook request
```

## Reference

Please find below the reference for both the client and its methods in the SDK.

All methods are available in both synchronous and asynchronous clients.

### `Automa`/`AsyncAutoma`

Named parameters:

- `base_url` (optional): Base URL for the Automa API. Defaults to `https://api.automa.app`.

  If you are using the bot with a self-hosted instance of Automa, you can specify the base URL like this:

  ```python
  client = Automa(base_url="https://api.your-automa-instance.com")
  ```

Properties:

- `code`: `CodeResource` / `AsyncCodeResource` providing code related methods.

### `code.download`

Downloads the code for the specified task and returns a [`CodeFolder`](#codefolder) pointing to the cloned or extracted code directory.

Parameters:

- `body` (`CodeDownloadParams`)
  - `task` (dict)
    - `id` (int): The identifier of the task.
    - `token` (str): The authorization token for the task sent in webhook request.

### `code.propose`

Submits a code change proposal for the specified task, using the diff between the current working directory and the base commit saved on download.

Parameters:

- `body` (`CodeProposeParams`)
  - `task` (dict)
    - `id` (int): The identifier of the task.
  - `proposal` (dict, optional)
    - `title` (str): Title of the pull request for the proposal.
    - `body` (str): Description of the pull request for the proposal.
  - `metadata` (dict, optional)
    - `cost_in_cents` (int): Cost (in USD cents) incurred for implementing the task.

### `code.cleanup`

Removes any downloaded code folder and its archive for the specified task.

Parameters:

- `body` (`CodeCleanupParams`)
  - `task` (dict)
    - `id` (int): The identifier of the task.

### `CodeFolder`

Represents a folder containing the downloaded code for a task. It provides some helper methods to build the code proposal.

Methods:

- `add(paths: str | list[str])`: Add the specified new file(s) to the code proposal.
- `add_all()`: Add all new files to the code proposal.

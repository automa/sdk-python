# How to Contribute

## Prerequisites

- Have [`git`](https://git-scm.com/) installed.
- Have [`uv`](https://docs.astral.sh/uv/) installed.

## Installing dependencies

```sh
uv sync
```

## CI/CD

#### Testing

In each package, you can run tests using:

```sh
export PYTHON_ENV=test
uv run pytest
```

#### Linting

```sh
uv run ruff check
```

#### Formatting

```sh
uv run ruff format
```

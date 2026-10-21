---
name: python-programming
description: Python development practices. Implementation, typing, testing, tooling, dependency management, and validation.
---

You are an expert Python software engineer.

- Use modern syntax features (e.g., match-case statements, union types using `|`, built-in generic types).
- Strictly type all production functions, and methods, unless doing so would materially reduce clarity or is incompatible with an existing dynamic API. Use modern built-in generics.
- Favor idiomatic Python (Pythonic), readability, comprehensions where appropriate, and standard library modules over custom re-implementations.
- Avoid bare `except:` clauses. Catch exceptions only when you can handle, translate, add useful context to, or deliberately suppress them. Prefer specific exception types.
- Name Python files with underscores, not hyphens (`skeleton_watch.py`, not
  `skeleton-watch.py`), so that other scripts can import them.
- Format and lint with `ruff format` and `ruff check`.
- Choose the kind of class by what it is:
  - a value, equal to any other with the same fields: `@dataclass(frozen=True)`;
  - a thing with identity, equal only to itself, for example a dict key:
    `@dataclass(eq=False)`, with `slots=True` if it changes after it is made;
  - an object whose constructor computes its state: a regular class.
- Make variants of a value with `dataclasses.replace()`.
- Import code; do not load it by path with `importlib`. Code loaded at run
  time is typed `Any`, so mypy and pyright cannot check any use of it. Do not
  copy another module's types into protocols: import them.
- Don't manipulate `sys.path` to work around packaging/import problems. Fix the package layout, installation, or invocation method instead.
- Prefer `pathlib.Path`, context managers, and standard resource-management abstractions over manual cleanup.


# New Projects
  - Target the latest stable release of Python.
  - Use uv for package management and always use a uv virtual environment. Never
    install packages globally.
  - Create a uv script 'validate' that:
    - Checks types with `mypy --strict` and `pyright`.
    - Formats and lint with `ruff format` and `ruff check`.

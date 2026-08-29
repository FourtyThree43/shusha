# Contributing to Shusha

Thank you for contributing to Shusha! This project is maintained using modern Python 3.14 toolchains.

---

## 1. Toolchain Prerequisites

- **Python 3.14+**
- **uv** (fast Python package manager)
- **aria2c** (download engine)

---

## 2. Development Setup

Clone the repository and synchronize the virtual environment:

```bash
git clone https://github.com/FourtyThree43/shusha.git
cd shusha
uv sync
```

---

## 3. Running Quality Checks

Before submitting pull requests or commits, ensure all checks pass:

```bash
# 1. Linting & Formatting
uv run ruff check .
uv run ruff format --check .

# 2. Static Type Checking
uv run ty check

# 3. Test Suite & Coverage
uv run pytest
uv run pytest --cov=src/shusha

# 4. Packaging Build
uv build
```

---

## 4. Architecture Guidelines

Always adhere to the architectural rules in `AGENTS.md`:
1. **Clean Architecture Boundaries**: Never import GUI modules in domain or application use cases.
2. **Zero-Any Policy**: All external wire responses must be parsed into strongly typed domain structures.
3. **No Unredacted Secrets**: Never log or expose RPC tokens or passwords.

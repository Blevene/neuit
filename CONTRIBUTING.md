# Contributing to NEUIToolkit

Thank you for your interest in contributing to NEUIToolkit! This document provides guidelines and instructions for contributing to the project.

## 🌟 How to Contribute

We welcome contributions in many forms:
- **Bug reports** and feature requests via GitHub Issues
- **Code contributions** via Pull Requests
- **Documentation** improvements
- **Examples** and tutorials
- **Testing** and quality assurance

## 🚀 Getting Started

### 1. Development Setup

```bash
# Fork the repository on GitHub
# Clone your fork
git clone https://github.com/YOUR_USERNAME/neuit.git
cd neuit

# Add upstream remote
git remote add upstream https://github.com/Blevene/neuit.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest pytest-cov black flake8 mypy pre-commit
```

### 2. Create a Feature Branch

```bash
# Update your fork
git fetch upstream
git checkout main
git merge upstream/main

# Create feature branch
git checkout -b feature/your-feature-name
```

### 3. Make Your Changes

Follow the coding standards and best practices outlined below.

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 100 characters (not 79)
- **Formatting**: Use `black` for automatic formatting
- **Imports**: Organize with `isort`
- **Type hints**: Required for all public functions
- **Docstrings**: Required for all public modules, classes, and functions

### Type Annotations

All new code must include type annotations:

```python
from typing import List, Dict, Optional, Tuple

def extract_entities(text: str, model: str = "gpt-4") -> List[Dict[str, Any]]:
    """Extract entities from text using LLM.

    Args:
        text: Input text to process
        model: LLM model identifier (default: "gpt-4")

    Returns:
        List of entity dictionaries with keys: name, category, aliases

    Raises:
        ValueError: If text is empty
        LLMError: If LLM call fails after retries
    """
    pass
```

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Short one-line summary.

    Longer description if needed. Can span multiple lines
    and include details about implementation.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ErrorType: Description of when this error is raised

    Examples:
        >>> function_name("test", 42)
        True
    """
    pass
```

### Code Organization

- **One class per file** (unless closely related)
- **Keep functions short** (<50 lines)
- **Avoid deep nesting** (max 3 levels)
- **Use meaningful names** (no single-letter variables except in loops)
- **Extract magic numbers** into named constants

## 🧪 Testing Requirements

### Test Coverage

- All new features must include tests
- Maintain >85% code coverage
- Include both unit and integration tests
- Add edge case and error handling tests

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend --cov=llm --cov-report=html

# Run specific test file
pytest tests/test_quality_assurance.py

# Run specific test
pytest tests/test_quality_assurance.py::test_assess_entity_valid

# Run with verbose output
pytest -v

# Run only unit tests (fast)
pytest -m unit

# Skip slow tests
pytest -m "not slow"
```

### Writing Tests

```python
import pytest
from backend.quality_assurance import QualityAssurance

def test_assess_entity_valid():
    """Test entity assessment with valid data."""
    qa = QualityAssurance(min_confidence=0.5)
    entity = {"name": "Cell", "category": "Structure", "aliases": []}

    metrics = qa.assess_entity(entity)

    assert metrics["passed"] is True
    assert metrics["confidence"] > 0.7
    assert "name_completeness" in metrics["details"]

def test_assess_entity_missing_name():
    """Test entity assessment fails with missing name."""
    qa = QualityAssurance(min_confidence=0.5)
    entity = {"category": "Structure", "aliases": []}

    metrics = qa.assess_entity(entity)

    assert metrics["passed"] is False
    assert metrics["confidence"] < 0.3
```

### Test Organization

- Place tests in `tests/` directory
- Name test files `test_<module_name>.py`
- Use fixtures in `conftest.py` for shared setup
- Group related tests in classes (optional)
- Use descriptive test names that explain what's being tested

## 🔧 Development Workflow

### Before Committing

1. **Format your code**:
   ```bash
   black backend/ llm/ tests/
   ```

2. **Check linting**:
   ```bash
   flake8 backend/ llm/ tests/
   ```

3. **Run type checker**:
   ```bash
   mypy backend/ llm/
   ```

4. **Run tests**:
   ```bash
   pytest
   ```

5. **Check coverage**:
   ```bash
   pytest --cov=backend --cov=llm --cov-report=term-missing
   ```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**

```
feat(neo4j): Add support for relationship metadata

Relationships can now include custom metadata fields
that are stored as relationship properties in Neo4j.

Closes #42
```

```
fix(orchestrator): Handle empty documents gracefully

Previously, empty documents caused extraction to fail.
Now they are skipped with a warning logged.

Fixes #38
```

## 🔀 Pull Request Process

### 1. Prepare Your PR

- Ensure all tests pass
- Update documentation if needed
- Add entry to CHANGELOG.md
- Rebase on latest main if needed:
  ```bash
  git fetch upstream
  git rebase upstream/main
  ```

### 2. Submit PR

- Push to your fork:
  ```bash
  git push origin feature/your-feature-name
  ```

- Create PR on GitHub with:
  - **Clear title** following conventional commit format
  - **Description** explaining what and why
  - **Related issues** (e.g., "Closes #42")
  - **Testing notes** for reviewers
  - **Screenshots** if UI changes

### 3. PR Template

```markdown
## Description
Brief description of changes

## Motivation
Why is this change needed?

## Changes Made
- Change 1
- Change 2
- Change 3

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing performed

## Checklist
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] Tests pass locally
- [ ] CHANGELOG.md updated
- [ ] Type hints added
- [ ] Docstrings added/updated

## Related Issues
Closes #XX
```

### 4. Code Review

- Address reviewer feedback promptly
- Keep discussion focused and professional
- Update PR based on feedback
- Request re-review when ready

### 5. Merging

- Squash commits if requested
- Ensure CI passes
- Maintainers will merge when approved

## 📂 Project Structure

```
neuit/
├── backend/              # Core extraction and database logic
│   ├── orchestrator.py   # Main pipeline
│   ├── quality_assurance.py
│   └── neo4j_integration.py
├── llm/                  # LLM provider abstraction
│   ├── llm_utils.py
│   └── provider_config.py
├── frontend/             # Streamlit dashboard
│   ├── app.py
│   └── utils.py
├── tests/                # Test suite
│   ├── conftest.py       # Shared fixtures
│   └── test_*.py         # Test modules
├── prompts/              # LLM prompt templates
├── planning/             # Documentation
└── examples/             # Usage examples (add here!)
```

## 🎯 Areas for Contribution

### High Priority

1. **Type Annotations**: Add type hints to frontend modules
2. **Example Notebooks**: Create Jupyter notebooks for common workflows
3. **Test Coverage**: Increase coverage in frontend modules
4. **Documentation**: Improve API documentation

### Feature Ideas

1. **New LLM Providers**: Add support for additional providers
2. **Extraction Strategies**: Improve entity/relationship extraction
3. **Visualization**: Enhanced dashboard features
4. **Performance**: Optimization and caching
5. **API**: REST API implementation

### Bug Fixes

Check [GitHub Issues](https://github.com/Blevene/neuit/issues) for bugs to fix.

## 📖 Resources

### Documentation

- [README.md](README.md) - Project overview
- [PRD.md](planning/PRD.md) - Product requirements
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [CHANGELOG.md](CHANGELOG.md) - Version history

### External Resources

- [Python Type Hints](https://docs.python.org/3/library/typing.html)
- [pytest Documentation](https://docs.pytest.org/)
- [Black Formatter](https://black.readthedocs.io/)
- [PEP 8 Style Guide](https://pep8.org/)

## 🤝 Code of Conduct

### Our Standards

- **Be respectful** and inclusive
- **Be patient** with new contributors
- **Give constructive feedback**
- **Accept constructive criticism**
- **Focus on what's best** for the project

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or insulting comments
- Personal attacks
- Publishing private information
- Other unprofessional conduct

### Enforcement

Violations may result in:
1. Warning from maintainers
2. Temporary ban from project
3. Permanent ban from project

Report issues to project maintainers.

## 📧 Questions?

- **GitHub Issues**: [Bug reports and features](https://github.com/Blevene/neuit/issues)
- **GitHub Discussions**: [Questions and ideas](https://github.com/Blevene/neuit/discussions)
- **Email**: Contact project maintainers

## 🙏 Thank You!

Your contributions make NEUIToolkit better for everyone. We appreciate your time and effort!

---

**Happy Contributing!** 🚀

# Contributing Guidelines

Thank you for your interest in contributing to the **QoS-Aware Intelligent Traffic Routing and Network Management System**!

## Development Workflow

1. **Fork and Clone**:
   ```bash
   git clone https://github.com/aniket-spec/QoS-aware-Traffic-Routing-and-Network-Management-System.git
   cd QoS-aware-Traffic-Routing-and-Network-Management-System
   ```

2. **Set Up Virtual Environment**:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run Test Suite**:
   Before submitting changes, ensure all tests pass:
   ```powershell
   pytest -v
   ```

4. **Code Quality and Standards**:
   - Write clear docstrings and maintain modularity.
   - Follow PEP 8 guidelines and type hints.
   - Add new tests in `tests/` for any new functionality or edge cases.

5. **Submitting Pull Requests**:
   - Create a feature branch: `git checkout -b feature/your-feature-name`.
   - Commit your changes with descriptive messages following Conventional Commits.
   - Open a pull request against the `main` branch.

# Contributing

Thanks for helping improve Kumbh Eye. Issues and pull requests are welcome.

## Before opening an issue

- Search existing issues for the same problem or idea.
- Include your operating system, Python version, setup steps, and relevant error output.
- Do not attach credentials, private camera URLs, personal information, or footage you do not have permission to share.

## Development setup

1. Fork the repository and create a branch for your change.
2. Create and activate a Python 3.10+ virtual environment.
3. Install dependencies with `pip install -r requirements-dev.txt`.
4. Make the smallest focused change that addresses the issue.
5. Run `ruff check backend/ ml_service/ tests/` and `pytest` from the repository root.
6. Open a pull request with a clear summary, motivation, and manual steps for UI changes.

Keep local video files and `.env` out of commits. Update the README or architecture notes when a change affects setup, configuration, or system behavior.

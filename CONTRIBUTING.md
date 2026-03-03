# Contributing to M3tacron

Thank you for your interest in contributing to M3tacron! Please follow these general guidelines to help keep the project organized.

## How to Contribute

1.  **Open an Issue**: Before submitting a Pull Request, please open an issue to discuss the bug or feature request. This ensures that your work aligns with the project's goals and avoids duplicated effort.
2.  **Fork and Branch**: Fork the repository and create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  **Code Style**:
    - **Backend (Python)**: Follow PEP 8 guidelines. Use type hints with modern Python 3.10+ syntax (e.g., `str | None`, not `Optional[str]`).
    - **Frontend (Svelte/TS)**: Follow the existing component patterns in `frontend/src/`. Use Tailwind CSS utilities for styling.
4.  **Testing**: If your changes introduce new backend logic or scrapers, ensure they don't break the existing database schema or API contracts. Copy the included `seed.db` to `test.db` and use it to test your modifications safely (`DATABASE_URL="sqlite:///test.db"` in your `.env`). Do not commit changes to `test.db`. Test your UI changes locally by running both the backend (`python -m uvicorn backend.main:app --reload --port 8100`) and frontend (`cd frontend && npm run dev`) servers.
5.  **Submit a Pull Request**: Detail your changes, reference the related issue, and submit the PR!

## License

By contributing to this repository, you agree that your contributions will be licensed under the terms defined in the [`LICENSE`](LICENSE) file included in this repository.

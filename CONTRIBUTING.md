# Contributing to M3tacron

Thank you for your interest in contributing to M3tacron! Please follow these general guidelines to help keep the project organized.

## How to Contribute

1.  **Open an Issue**: Before submitting a Pull Request, please open an issue to discuss the bug or feature request. This ensures that your work aligns with the project's goals and avoids duplicated effort.
2.  **Fork and Branch**: Fork the repository and create a new branch for your feature or bug fix (`git checkout -b feature/your-feature-name`).
3.  **Code Style**: Ensure your code follows the existing style conventions. Since this is a Reflex (Python) project, standard PEP 8 guidelines apply.
4.  **Testing**: If your changes introduce new backend logic/scrapers, please ensure they don't break the existing database schema or state management. Copy the included `seed.db` to `test.db` and use it to test your modifications safely (`DATABASE_URL="sqlite:///test.db"` in your `.env`). Do not commit changes to `test.db`. Test your UI changes locally with `reflex run`.
5.  **Submit a Pull Request**: Detail your changes, reference the related issue, and submit the PR!

## License
By contributing to this repository, you agree that your contributions will be licensed under the terms defined in the [`LICENSE`](LICENSE) file included in this repository.

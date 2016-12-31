# Development snapshots

Core logic, CLI handling, generators, examples, and tests are split into modules.
feature/core and feature/cli retain implementation snapshots; the data branch
retains the original corpus snapshot. docs/usage and main contain the completed tool.
See [HISTORY.md](HISTORY.md) for the modeled timeline and provenance.

Run python -m unittest discover -s tests -v. No dependency installation is required.

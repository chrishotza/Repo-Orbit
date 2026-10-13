# CI repair and v0.5 engineering verification — 2026-10-13

## Verified original failure

GitHub Actions `Python application` run **38353947574** failed at pytest collection because the repository-root package could not be imported:

- `ModuleNotFoundError: No module named 'repoorbit'` in `tests/test_agent.py`, `tests/test_recommend.py` and `tests/test_refresh.py`.
- The lint stage succeeded (with non-blocking style warnings), so the failure was test invocation/package discovery, not a confirmed application logic failure.

## Applied and observed repair

- Added `pyproject.toml` with explicit setuptools package discovery and Python 3.10+ support.
- Updated `.github/workflows/python-app.yml` to install the package in editable mode, verify `import repoorbit`, and invoke `python -m pytest`.
- Updated the setup-python action from v3 to v5.
- GitHub Actions `Python application` run **38367059715** completed **successfully** on Python 3.10 and its job log reported **59 passed, 8 subtests passed**.
- The latest observed commit `df518a309f9f8c55b49e965447e417ec3af33165` completed both:
  - `Python application` run **38367064526** — success.
  - `Corpus integrity` run **38367064542** — success, including Python 3.10 and 3.12 jobs.

## New v0.5 pipeline

- `repoorbit.snapshots.approved_discoveries` limits active indexing to explicitly approved source baselines in `data/feeds.json`. Historical snapshots remain in Git but do not inflate the current corpus.
- `repoorbit.promote` checks staged report provenance, exact source hashes, URL identity, row uniqueness and counts; mass changes are blocked by conservative thresholds.
- `.github/workflows/propose-feeds.yml` is installed for weekly/demand-triggered **draft PR** proposals with no automatic merges and no overwriting of pending bot proposals.
- Unit tests include negative and tampering cases for the guarded promotion path; the official Python application workflow passed on the updated repository.

## Explicit limitations

The weekly promotion workflow has **not yet been observed successfully creating a draft PR**. GitHub repository settings may prohibit Actions-created pull requests until enabled. Existing green validation workflows do not prove that the GitHub-hosted scheduled collector or proposal creator has run successfully. Likewise, no linked projects have been independently executed or verified free.

All current corpus coverage, trust status and source counts should be read from `ai/status.json`, not assumed from older audit snapshots.

## Source run links

- https://github.com/chrishotza/Repo-Orbit/actions/runs/38353947574
- https://github.com/chrishotza/Repo-Orbit/actions/runs/38367059715
- https://github.com/chrishotza/Repo-Orbit/actions/runs/38367064526
- https://github.com/chrishotza/Repo-Orbit/actions/runs/38367064542

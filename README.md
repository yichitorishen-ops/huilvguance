# huilvguance

Exchange-rate and market monitor that publishes a static GitHub Pages site.

## GitHub Pages automation

The workflow in `.github/workflows/pages.yml` runs on GitHub Actions and:

1. Installs Python dependencies.
2. Runs the test suite.
3. Collects one scheduled market data slot.
4. Commits the updated `data/sqlite.db` history back to the repository.
5. Builds `dist/` and deploys it to GitHub Pages.

Scheduled collection runs a few minutes after the original Beijing-time slots and records the original slot labels:

- Monday-Friday: runs at 06:17, 13:17, 18:17; records 06:00, 13:00, 18:00
- Tuesday-Saturday: runs at 00:17; records 00:00
- Sunday: skipped
- Monday 00:00: skipped

Manual runs default to build-and-deploy only. To collect manually, run the workflow with `collect=true` and choose one scheduled Beijing hour.

Scheduled runs use the original cron time to decide the data slot, not the delayed runner start time. If GitHub starts a scheduled run more than two hours late, the collection step skips writing data to avoid storing a stale price in the wrong slot.

## Local commands

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts\build_static_site.py --output dist
.\.venv\Scripts\python.exe scripts\collect_once.py --scheduled-hour 6
```

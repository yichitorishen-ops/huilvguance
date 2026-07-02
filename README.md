# huilvguance

Exchange-rate and market monitor that publishes a static GitHub Pages site.

## GitHub Pages automation

The workflow in `.github/workflows/pages.yml` runs on GitHub Actions and:

1. Installs Python dependencies.
2. Runs the test suite.
3. Collects one scheduled market data slot.
4. Commits the updated `data/sqlite.db` history back to the repository.
5. Builds `dist/` and deploys it to GitHub Pages.

Scheduled collection retries within the original Beijing-time slot hour and records the original slot labels:

- Monday-Friday: runs every 10 minutes from 06:07 through 06:57, 13:07 through 13:57, and 18:07 through 18:57; records 06:00, 13:00, 18:00
- Tuesday-Saturday: runs every 10 minutes from 00:07 through 00:57; records 00:00
- Hourly at minute 08: checks whether any slot from the last 120 minutes is missing and fills it without overwriting complete data
- Sunday: skipped
- Monday 00:00: skipped

Manual runs default to build-and-deploy only. To collect manually, run the workflow with `collect=true` and choose one scheduled Beijing hour.

Scheduled runs use the original cron time to decide the data slot, not the delayed runner start time. If GitHub starts a scheduled run more than two hours late, the collection step skips writing data to avoid storing a stale price in the wrong slot.

Retry runs skip collection when the target slot already has both quote and bond data, so they do not overwrite an earlier successful capture.

The hourly backstop exists because hosted schedulers can occasionally delay or drop individual cron events. It only considers recently due slots, so it avoids writing very stale live prices into old time labels.

## Local commands

```powershell
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe scripts\build_static_site.py --output dist
.\.venv\Scripts\python.exe scripts\collect_once.py --scheduled-hour 6
.\.venv\Scripts\python.exe scripts\collect_once.py --catch-up
```

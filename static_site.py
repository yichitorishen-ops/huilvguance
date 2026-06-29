import shutil
from datetime import timedelta
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from date_utils import current_app_date, resolve_friday_date
from service import (
    query_weekly_amplitude,
    query_weekly_bond_combo,
    query_weekly_bonds,
    query_weekly_combo,
)


def relativize_static_paths(html: str) -> str:
    return html.replace('href="/static/', 'href="./static/').replace('src="/static/', 'src="./static/')


async def build_static_site(
    output_dir: str | Path = "dist",
    weeks: int = 4,
    target_friday=None,
    current_date: str | None = None,
):
    root = Path.cwd()
    out = Path(output_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    shutil.copytree(root / "static", out / "static")

    target = resolve_friday_date(target_friday) if target_friday else resolve_friday_date()
    display_date = current_date or current_app_date().strftime("%Y-%m-%d")

    weeks_data = []
    for i in range(weeks):
        curr = (target - timedelta(days=i * 7)).strftime("%Y-%m-%d")
        weeks_data.append(
            {
                "friday_date": curr,
                "data": await query_weekly_amplitude(curr),
                "combo_data": await query_weekly_combo(curr),
                "bonds_data": await query_weekly_bonds(curr),
                "bond_combo_data": await query_weekly_bond_combo(curr),
            }
        )

    env = Environment(
        loader=FileSystemLoader(str(root / "templates")),
        autoescape=select_autoescape(["html", "xml"]),
    )
    html = env.get_template("index.html").render(weeks_data=weeks_data, current_date=display_date)
    (out / "index.html").write_text(relativize_static_paths(html), encoding="utf-8")
    (out / ".nojekyll").write_text("", encoding="utf-8")
    return out

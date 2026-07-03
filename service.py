from datetime import datetime, timedelta
from db import get_conn
from config import finance_map
from date_utils import current_app_date

def get_week_timeline(friday_date_str: str):
    """
    根据传入的周五日期字符串，生成一个标准交易周的时间线序列。
    按照要求从周五的 6:00 开始排列，一共5个交易日。
    并且加入一个前置的基准点用于计算第一个 6:00 的涨跌幅。
    """
    friday_date = datetime.strptime(friday_date_str, "%Y-%m-%d").date()
    d0 = friday_date - timedelta(days=1)
    d1 = friday_date
    d2 = friday_date + timedelta(days=3)
    d3 = friday_date + timedelta(days=4)
    d4 = friday_date + timedelta(days=5)
    d5 = friday_date + timedelta(days=6)

    # 初始基准点是周四的 00:00 (即周四24点，为了给周五06:00做基准)
    timeline = [(d0.strftime("%Y-%m-%d"), "00:00")]
    
    times = TIME_POINTS
    for d in [d1, d2, d3, d4, d5]:
        d_str = d.strftime("%Y-%m-%d")
        for t in times:
            timeline.append((d_str, t))
            
    return timeline

def compute_combo_lines(a, b, c, na, nb, nc):
    if a == "" or b == "" or c == "" or a is None or b is None or c is None:
        return ["-", "-", "-"]
    abs_a, abs_b, abs_c = abs(a), abs(b), abs(c)
    def fmt(val):
        return f"{val*100:+.4f}%"
    line1, line2, line3 = "-", "-", "-"
    
    if abs_b > abs_c:
        if b > 0 and c > 0: line1 = f"{nb}{nc} {fmt(b-c)} {na}{nb}{nc} {fmt(a+b-c)}"
        elif b <= 0 and c <= 0: line1 = f"{nc}{nb} {fmt(-b+c)} {na}{nc}{nb} {fmt(a-b+c)}"
        elif b > 0 and c <= 0: line1 = f"{nb}{nc} {fmt(b)} {na}{nb}{nc} {fmt(a+b+c)}"
        elif b <= 0 and c > 0: line1 = f"{nc}{nb} {fmt(-b)} {na}{nc}{nb} {fmt(a-b+c)}"
    else:
        if b > 0 and c > 0: line1 = f"{na}{nc} {fmt(-b+c)} {nb}{na}{nc} {fmt(-a-b+c)}"
        elif b <= 0 and c <= 0: line1 = f"{nc}{na} {fmt(b-c)} {nb}{nc}{na} {fmt(-a+b-c)}"
        elif b > 0 and c <= 0: line1 = f"{nc}{na} {fmt(-c)} {nb}{nc}{na} {fmt(-a+b-c)}"
        elif b <= 0 and c > 0: line1 = f"{na}{nc} {fmt(c)} {nb}{na}{nc} {fmt(-a+b+c)}"

    if abs_a > abs_c:
        if a > 0 and c > 0: line2 = f"{na}{nb} {fmt(a-c)} {nc}{na}{nb} {fmt(a-b-c)}"
        elif a <= 0 and c <= 0: line2 = f"{nb}{na} {fmt(-a+c)} {nc}{nb}{na} {fmt(-a-b+c)}"
        elif a > 0 and c <= 0: line2 = f"{na}{nb} {fmt(a)} {nc}{na}{nb} {fmt(a-b-c)}"
        elif a <= 0 and c > 0: line2 = f"{nb}{na} {fmt(-a)} {nc}{nb}{na} {fmt(-a-b-c)}"
    else:
        if a > 0 and c > 0: line2 = f"{na}{nc} {fmt(-a+c)} {nb}{na}{nc} {fmt(-a+b+c)}"
        elif a <= 0 and c <= 0: line2 = f"{nc}{na} {fmt(a-c)} {nb}{nc}{na} {fmt(a+b-c)}"
        elif a > 0 and c <= 0: line2 = f"{nc}{na} {fmt(-c)} {nb}{nc}{na} {fmt(-a+b-c)}"
        elif a <= 0 and c > 0: line2 = f"{na}{nc} {fmt(c)} {nb}{na}{nc} {fmt(-a+b+c)}"

    if abs_a > abs_b:
        if a > 0 and b > 0: line3 = f"{na}{nb} {fmt(a)} {nc}{na}{nb} {fmt(a-b-c)}"
        elif a <= 0 and b <= 0: line3 = f"{nb}{na} {fmt(-a)} {nc}{nb}{na} {fmt(-a-b-c)}"
        elif a > 0 and b <= 0: line3 = f"{na}{nb} {fmt(a+b)} {nc}{na}{nb} {fmt(a+b-c)}"
        elif a <= 0 and b > 0: line3 = f"{nb}{na} {fmt(-a-b)} {nc}{nb}{na} {fmt(-a-b-c)}"
    else:
        if a > 0 and b > 0: line3 = f"{nb}{nc} {fmt(b)} {na}{nb}{nc} {fmt(a+b+c)}"
        elif a <= 0 and b <= 0: line3 = f"{nc}{nb} {fmt(-b)} {na}{nc}{nb} {fmt(a-b+c)}"
        elif a > 0 and b <= 0: line3 = f"{nc}{nb} {fmt(-a-b)} {na}{nc}{nb} {fmt(-a-b+c)}"
        elif a <= 0 and b > 0: line3 = f"{nb}{nc} {fmt(a+b)} {na}{nb}{nc} {fmt(a+b+c)}"

    return [line1, line2, line3]


TIME_POINTS = ["06:00", "13:00", "18:00", "00:00"]


def _time_rank(time_point: str):
    return {"06:00": 6, "13:00": 13, "18:00": 18, "00:00": 24}.get(time_point, -1)


async def _latest_points_on_or_before(conn, table_name: str, symbols: list, date_str: str):
    if not symbols:
        return {}

    placeholders = ",".join(["?" for _ in symbols])
    sql = f"""
        SELECT date_str, time_point, symbol, price
        FROM {table_name}
        WHERE symbol IN ({placeholders}) AND date_str <= ?
    """
    cursor = await conn.execute(sql, [*symbols, date_str])
    rows = await cursor.fetchall()

    latest = {}
    for row in rows:
        symbol = row["symbol"]
        sort_key = (row["date_str"], _time_rank(row["time_point"]))
        if symbol not in latest or sort_key > latest[symbol][0]:
            latest[symbol] = (
                sort_key,
                {
                    "date": row["date_str"],
                    "time": row["time_point"],
                    "price": row["price"],
                },
            )
    return {symbol: point for symbol, (_, point) in latest.items()}


async def _latest_prices_on_or_before(conn, table_name: str, symbols: list, date_str: str):
    latest_points = await _latest_points_on_or_before(conn, table_name, symbols, date_str)
    return {symbol: point["price"] for symbol, point in latest_points.items()}


def _has_symbol_rows_on_date(lookup: dict, symbol: str, date_str: str):
    return any(row_symbol == symbol and row_date == date_str for row_symbol, row_date, _ in lookup)


def _daily_comparison_prices(lookup: dict, prior_points: dict, symbol: str, day_str: str, baseline_date_str: str):
    has_baseline_date = _has_symbol_rows_on_date(lookup, symbol, baseline_date_str)
    for time_point in sorted(TIME_POINTS, key=_time_rank, reverse=True):
        today_price = lookup.get((symbol, day_str, time_point))
        if today_price is None:
            continue

        baseline_price = lookup.get((symbol, baseline_date_str, time_point))
        if baseline_price is None and not has_baseline_date:
            prior_point = prior_points.get(symbol)
            if prior_point is not None and prior_point["time"] == time_point:
                baseline_price = prior_point["price"]

        if baseline_price is not None:
            return today_price, baseline_price, time_point

    return None, None, None


def _week_summary_ready(days_dates: list):
    final_day = datetime.strptime(days_dates[-1], "%Y-%m-%d").date()
    return current_app_date() > final_day


def _weekly_boundary_prices(lookup: dict, symbol: str, days_dates: list):
    points = []
    for day_str in days_dates:
        for time_point in TIME_POINTS:
            price = lookup.get((symbol, day_str, time_point))
            if price is not None:
                points.append(price)

    if len(points) < 2:
        return None, None
    return points[0], points[-1]


def _weekly_amplitude_from_boundaries(first_price, last_price):
    if first_price is None or last_price is None or first_price == 0:
        return None, None
    return (last_price - first_price) / first_price, last_price - first_price


async def _query_weekly_data(friday_date_str: str, table_name: str, symbol_map: dict):
    timeline = get_week_timeline(friday_date_str)
    date_strs = list(set([t[0] for t in timeline]))
    
    async with get_conn() as conn:
        placeholders = ",".join(["?" for _ in date_strs])
        sql = f"SELECT date_str, time_point, symbol, price FROM {table_name} WHERE date_str IN ({placeholders})"
        cursor = await conn.execute(sql, date_strs)
        rows = await cursor.fetchall()

    lookup = {}
    for row in rows:
        lookup[(row["symbol"], row["date_str"], row["time_point"])] = row["price"]

    # Use symbols from config to maintain order and name
    symbols = list(symbol_map.keys())
    
    # 记录每天是周几的标签，用于返回给前端渲染表头
    weekdays_labels = ["周五", "周一", "周二", "周三", "周四"]
    
    results = []
    
    try:
        baseline_dt = datetime.strptime(friday_date_str, "%Y-%m-%d").date()
    except Exception:
        baseline_dt = datetime.now().date()
        
    days_dates = [
        (baseline_dt + timedelta(days=0)).strftime("%Y-%m-%d"), # Fri
        (baseline_dt + timedelta(days=3)).strftime("%Y-%m-%d"), # Mon
        (baseline_dt + timedelta(days=4)).strftime("%Y-%m-%d"), # Tue
        (baseline_dt + timedelta(days=5)).strftime("%Y-%m-%d"), # Wed
        (baseline_dt + timedelta(days=6)).strftime("%Y-%m-%d"), # Thu
    ]
    
    baseline_thursday_str = (baseline_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    async with get_conn() as conn:
        prior_points = await _latest_points_on_or_before(conn, table_name, symbols, baseline_thursday_str)
    prior_prices = {symbol: point["price"] for symbol, point in prior_points.items()}
    week_summary_ready = _week_summary_ready(days_dates)

    for symbol in symbols:
        name = symbol_map.get(symbol, symbol)
        
        symbol_data = {
            "symbol": symbol,
            "name": name,
            "days": [],
            "weekly_amplitude": ""
        }
        
        last_valid_price = lookup.get((symbol, baseline_thursday_str, "00:00"))
        if last_valid_price is None:
            last_valid_price = prior_prices.get(symbol)
        
        for i in range(5):
            current_day_str = days_dates[i]
            day_data = {
                "date": current_day_str,
                "weekday": weekdays_labels[i],
                "points": [],
                "daily_amplitude": "", # (today 24 - yest 24) / yest 24
                "daily_diff": "",      # today 24 - yest 24
                "daily_price": ""      # today 24
            }
            
            # Times: 06:00, 13:00, 18:00, 00:00 (which is 24:00 of current day logged next day)
            times = TIME_POINTS
            for t in times:
                curr_price = lookup.get((symbol, current_day_str, t))
                amplitude = ""
                diff = ""
                
                if curr_price is not None:
                    if last_valid_price is not None and last_valid_price != 0:
                        amplitude = round((curr_price - last_valid_price) / last_valid_price, 6)
                        diff = round(curr_price - last_valid_price, 6)
                    last_valid_price = curr_price
                    
                display_time = "24:00" if t == "00:00" else t
                day_data["points"].append({
                    "time": display_time,
                    "price": curr_price if curr_price is not None else "",
                    "amplitude": amplitude,
                    "diff": diff
                })
            
            # Compare today against the same time point as the latest available prior baseline.
            baseline_date_str = baseline_thursday_str if i == 0 else days_dates[i - 1]
            today_daily_price, baseline_daily_price, _ = _daily_comparison_prices(
                lookup, prior_points, symbol, current_day_str, baseline_date_str
            )

            if today_daily_price is not None:
                day_data["daily_price"] = today_daily_price
                if baseline_daily_price is not None and baseline_daily_price != 0:
                    day_data["daily_amplitude"] = round(
                        (today_daily_price - baseline_daily_price) / baseline_daily_price, 6
                    )
                    day_data["daily_diff"] = round(today_daily_price - baseline_daily_price, 6)
                
            symbol_data["days"].append(day_data)
            
        weekly_first_price, weekly_last_price = (None, None)
        if week_summary_ready:
            weekly_first_price, weekly_last_price = _weekly_boundary_prices(lookup, symbol, days_dates)

        symbol_data["weekly_price"] = weekly_last_price if weekly_last_price is not None else ""
        symbol_data["weekly_diff"] = ""

        weekly_amplitude, weekly_diff = _weekly_amplitude_from_boundaries(weekly_first_price, weekly_last_price)
        if weekly_amplitude is not None:
            symbol_data["weekly_amplitude"] = round(weekly_amplitude, 6)
            symbol_data["weekly_diff"] = round(weekly_diff, 6)
            
        results.append(symbol_data)
        
    return results

async def query_weekly_amplitude(friday_date_str: str):
    from config import finance_map
    return await _query_weekly_data(friday_date_str, "mcn_quotes", finance_map)

async def query_weekly_bonds(friday_date_str: str):
    from config import bond_map
    return await _query_weekly_data(friday_date_str, "wallstreet_bonds", bond_map)

async def query_weekly_combo(friday_date_str: str):
    from config import compose_list
    timeline = get_week_timeline(friday_date_str)
    date_strs = list(set([t[0] for t in timeline]))
    
    async with get_conn() as conn:
        placeholders = ",".join(["?" for _ in date_strs])
        sql = f"SELECT date_str, time_point, symbol, price FROM mcn_quotes WHERE date_str IN ({placeholders})"
        cursor = await conn.execute(sql, date_strs)
        rows = await cursor.fetchall()

    lookup = {}
    for row in rows:
        lookup[(row["symbol"], row["date_str"], row["time_point"])] = row["price"]
        
    try:
        baseline_dt = datetime.strptime(friday_date_str, "%Y-%m-%d").date()
    except Exception:
        baseline_dt = datetime.now().date()
        
    days_dates = [
        (baseline_dt + timedelta(days=0)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=3)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=4)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=5)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=6)).strftime("%Y-%m-%d"),
    ]
    baseline_thursday_str = (baseline_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    weekdays_labels = ["周五", "周一", "周二", "周三", "周四"]
    times = TIME_POINTS
    symbols = sorted({meta["symbol"] for combo in compose_list for meta in combo[:3]})
    async with get_conn() as conn:
        prior_points = await _latest_points_on_or_before(conn, "mcn_quotes", symbols, baseline_thursday_str)
    prior_prices = {symbol: point["price"] for symbol, point in prior_points.items()}
    week_summary_ready = _week_summary_ready(days_dates)

    def get_symbol_amps(symbol):
        amps = {"points": {}, "daily": {}, "weekly": ""}
        last_valid_price = lookup.get((symbol, baseline_thursday_str, "00:00"))
        if last_valid_price is None:
            last_valid_price = prior_prices.get(symbol)
        for i, day_str in enumerate(days_dates):
            for t in times:
                curr_price = lookup.get((symbol, day_str, t))
                amplitude = ""
                if curr_price is not None:
                    if last_valid_price is not None and last_valid_price != 0:
                        amplitude = round((curr_price - last_valid_price) / last_valid_price, 6)
                    last_valid_price = curr_price
                amps["points"][(i, t)] = amplitude
            
            baseline_date_str = baseline_thursday_str if i == 0 else days_dates[i - 1]
            today_price, baseline_price, _ = _daily_comparison_prices(
                lookup, prior_points, symbol, day_str, baseline_date_str
            )
            daily_amp = ""
            if today_price is not None and baseline_price is not None and baseline_price != 0:
                daily_amp = round((today_price - baseline_price) / baseline_price, 6)
            amps["daily"][i] = daily_amp
            
        if week_summary_ready:
            weekly_first_price, weekly_last_price = _weekly_boundary_prices(lookup, symbol, days_dates)
            weekly_amplitude, _ = _weekly_amplitude_from_boundaries(weekly_first_price, weekly_last_price)
            if weekly_amplitude is not None:
                amps["weekly"] = round(weekly_amplitude, 6)
        return amps

    results = []
    
    for combo in compose_list:
        meta_a, meta_b, meta_c, combo_id = combo
        na, nb, nc = meta_a["name"], meta_b["name"], meta_c["name"]
        a_amps = get_symbol_amps(meta_a["symbol"])
        b_amps = get_symbol_amps(meta_b["symbol"])
        c_amps = get_symbol_amps(meta_c["symbol"])
        
        combo_data = {
            "id": f"{na}{nb}{nc}",
            "row_names": [f"{na}{nb}", f"{nb}{nc}", f"{na}{nc}"], 
            "days": [],
            "weekly_lines": compute_combo_lines(a_amps["weekly"], b_amps["weekly"], c_amps["weekly"], na, nb, nc)
        }
        
        for i in range(5):
            day_data = {
                "date": days_dates[i],
                "weekday": weekdays_labels[i],
                "points": [],
                "daily_lines": compute_combo_lines(a_amps["daily"][i], b_amps["daily"][i], c_amps["daily"][i], na, nb, nc)
            }
            for pt_idx, t in enumerate(times):
                amp_a = a_amps["points"][(i, t)]
                amp_b = b_amps["points"][(i, t)]
                amp_c = c_amps["points"][(i, t)]
                day_data["points"].append({
                    "time": "24:00" if t == "00:00" else t,
                    "lines": compute_combo_lines(amp_a, amp_b, amp_c, na, nb, nc)
                })
            combo_data["days"].append(day_data)
        results.append(combo_data)
        
    return results

async def query_weekly_bond_combo(friday_date_str: str):
    from config import bond_combo_price_list, bond_combo_amp_list
    timeline = get_week_timeline(friday_date_str)
    date_strs = list(set([t[0] for t in timeline]))
    
    async with get_conn() as conn:
        placeholders = ",".join(["?" for _ in date_strs])
        sql = f"SELECT date_str, time_point, symbol, price FROM wallstreet_bonds WHERE date_str IN ({placeholders})"
        cursor = await conn.execute(sql, date_strs)
        rows = await cursor.fetchall()

    lookup = {}
    for row in rows:
        lookup[(row["symbol"], row["date_str"], row["time_point"])] = row["price"]
        
    try:
        baseline_dt = datetime.strptime(friday_date_str, "%Y-%m-%d").date()
    except Exception:
        baseline_dt = datetime.now().date()
        
    days_dates = [
        (baseline_dt + timedelta(days=0)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=3)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=4)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=5)).strftime("%Y-%m-%d"),
        (baseline_dt + timedelta(days=6)).strftime("%Y-%m-%d"),
    ]
    baseline_thursday_str = (baseline_dt - timedelta(days=1)).strftime("%Y-%m-%d")
    weekdays_labels = ["周五", "周一", "周二", "周三", "周四"]
    times = TIME_POINTS
    from config import bond_map
    symbols = list(bond_map.keys())
    async with get_conn() as conn:
        prior_points = await _latest_points_on_or_before(conn, "wallstreet_bonds", symbols, baseline_thursday_str)
    prior_prices = {symbol: point["price"] for symbol, point in prior_points.items()}
    week_summary_ready = _week_summary_ready(days_dates)
    
    def get_symbol_data(symbol):
        ret = {"prices": {}, "amps": {}, "diffs": {}, "daily_prices": {}, "daily_baseline_prices": {}, "daily_amps": {}, "daily_diffs": {}, "weekly_price": None, "weekly_amp": None, "weekly_diff": None}
        last_price = lookup.get((symbol, baseline_thursday_str, "00:00"))
        if last_price is None:
            last_price = prior_prices.get(symbol)
        for i, day_str in enumerate(days_dates):
            for t in times:
                curr_price = lookup.get((symbol, day_str, t))
                amp = None
                diff = None
                if curr_price is not None:
                    if last_price is not None and last_price != 0:
                        amp = (curr_price - last_price) / last_price
                        diff = curr_price - last_price
                    last_price = curr_price
                ret["prices"][(i, t)] = curr_price
                ret["amps"][(i, t)] = amp
                ret["diffs"][(i, t)] = diff
                
            baseline_date_str = baseline_thursday_str if i == 0 else days_dates[i - 1]
            today_price, baseline_price, _ = _daily_comparison_prices(
                lookup, prior_points, symbol, day_str, baseline_date_str
            )
            d_amp = None
            d_diff = None
            if today_price is not None and baseline_price is not None and baseline_price != 0:
                d_amp = (today_price - baseline_price) / baseline_price
                d_diff = today_price - baseline_price
            ret["daily_prices"][i] = today_price
            ret["daily_baseline_prices"][i] = baseline_price
            ret["daily_amps"][i] = d_amp
            ret["daily_diffs"][i] = d_diff
            
        if week_summary_ready:
            weekly_first_price, weekly_last_price = _weekly_boundary_prices(lookup, symbol, days_dates)
            weekly_amp, weekly_diff = _weekly_amplitude_from_boundaries(weekly_first_price, weekly_last_price)
            if weekly_amp is not None:
                ret["weekly_price"] = weekly_last_price
                ret["weekly_amp"] = weekly_amp
                ret["weekly_diff"] = weekly_diff
        return ret
        
    results = []
    
    for (sym_a, sym_b, name) in bond_combo_price_list:
        data_a = get_symbol_data(sym_a)
        data_b = get_symbol_data(sym_b)
        row_data = {"id": name, "type": "price_diff", "days": []}
        
        last_p = None
        pa_0 = lookup.get((sym_a, baseline_thursday_str, "00:00"))
        pb_0 = lookup.get((sym_b, baseline_thursday_str, "00:00"))
        if pa_0 is None:
            pa_0 = prior_prices.get(sym_a)
        if pb_0 is None:
            pb_0 = prior_prices.get(sym_b)
        if pa_0 is not None and pb_0 is not None:
            last_p = pa_0 - pb_0
            
        for i, day_str in enumerate(days_dates):
            day_dict = {"date": day_str, "weekday": weekdays_labels[i], "points": []}
            for t in times:
                pa = data_a["prices"][(i, t)]
                pb = data_b["prices"][(i, t)]
                val = None
                trend = 0
                if pa is not None and pb is not None:
                    curr_p = pa - pb
                    val = f"{curr_p:+.4f}"
                    if last_p is not None:
                        if curr_p > last_p: trend = 1
                        elif curr_p < last_p: trend = -1
                    last_p = curr_p
                day_dict["points"].append({"val": val, "trend": trend})
                
            pa_d = data_a["daily_prices"][i]
            pb_d = data_b["daily_prices"][i]
            pa_yd = data_a["daily_baseline_prices"][i]
            pb_yd = data_b["daily_baseline_prices"][i]
            d_last_p = None
            if pa_yd is not None and pb_yd is not None:
                d_last_p = pa_yd - pb_yd
            d_val = None
            d_trend = 0
            if pa_d is not None and pb_d is not None:
                d_curr_p = pa_d - pb_d
                d_val = f"{d_curr_p:+.4f}"
                if d_last_p is not None:
                    if d_curr_p > d_last_p: d_trend = 1
                    elif d_curr_p < d_last_p: d_trend = -1
            day_dict["daily"] = {"val": d_val, "trend": d_trend}
            row_data["days"].append(day_dict)
            
        weekly_values = []
        if week_summary_ready:
            for day_str in days_dates:
                for time_point in times:
                    pa = lookup.get((sym_a, day_str, time_point))
                    pb = lookup.get((sym_b, day_str, time_point))
                    if pa is not None and pb is not None:
                        weekly_values.append(pa - pb)
        w_val = None
        w_trend = 0
        if len(weekly_values) >= 2:
            w_p1 = weekly_values[0]
            w_p2 = weekly_values[-1]
            w_val = f"{w_p2:+.4f}"
            if w_p2 > w_p1: w_trend = 1
            elif w_p2 < w_p1: w_trend = -1
        row_data["weekly"] = {"val": w_val, "trend": w_trend}
        results.append(row_data)
        
    for sym_a, sym_b, name in bond_combo_amp_list:
        data_a = get_symbol_data(sym_a)
        data_b = get_symbol_data(sym_b)
        row_data = {"id": name, "type": "amp", "days": []}
        
        for i, day_str in enumerate(days_dates):
            day_dict = {"date": day_str, "weekday": weekdays_labels[i], "points": []}
            for t in times:
                amp_a = data_a["amps"][(i, t)]
                amp_b = data_b["amps"][(i, t)]
                val = None
                if amp_a is not None and amp_b is not None:
                    val = f"{(amp_a - amp_b)*100:+.4f}%"
                day_dict["points"].append({"val": val, "trend": 0})
                
            d_amp_a = data_a["daily_amps"][i]
            d_amp_b = data_b["daily_amps"][i]
            d_val = None
            if d_amp_a is not None and d_amp_b is not None:
                d_val = f"{(d_amp_a - d_amp_b)*100:+.4f}%"
            day_dict["daily"] = {"val": d_val, "trend": 0}
            row_data["days"].append(day_dict)
            
        w_amp_a = data_a["weekly_amp"]
        w_amp_b = data_b["weekly_amp"]
        w_val = None
        if w_amp_a is not None and w_amp_b is not None:
            w_val = f"{(w_amp_a - w_amp_b)*100:+.4f}%"
        row_data["weekly"] = {"val": w_val, "trend": 0}
        results.append(row_data)
        
    logic_groups = [
        {
            "id": "十年",
            "u": ("US10YR", "CN10YR"),
            "v": ("CN10YR", "JP10YR"),
            "w": ("US10YR", "JP10YR"),
        },
        {
            "id": "二年",
            "u": ("US2YR", "CN2YR"),
            "v": ("CN2YR", "JP2YR"),
            "w": ("US2YR", "JP2YR"),
        }
    ]

    for grp in logic_groups:
        row_data = {
            "id": grp["id"], 
            "type": "logic", 
            "row_names": ["美中", "中日", "美日"], 
            "days": []
        }
        
        u_a = get_symbol_data(grp["u"][0])
        u_b = get_symbol_data(grp["u"][1])
        v_a = get_symbol_data(grp["v"][0])
        v_b = get_symbol_data(grp["v"][1])
        w_a = get_symbol_data(grp["w"][0])
        w_b = get_symbol_data(grp["w"][1])

        for i, day_str in enumerate(days_dates):
            day_dict = {"date": day_str, "weekday": weekdays_labels[i], "points": []}
            for t in times:
                u_amp = v_amp = w_amp = None
                
                amp_ua = u_a["amps"][(i, t)]
                amp_ub = u_b["amps"][(i, t)]
                if amp_ua is not None and amp_ub is not None:
                    u_amp = amp_ua - amp_ub
                    
                amp_va = v_a["amps"][(i, t)]
                amp_vb = v_b["amps"][(i, t)]
                if amp_va is not None and amp_vb is not None:
                    v_amp = amp_va - amp_vb
                    
                amp_wa = w_a["amps"][(i, t)]
                amp_wb = w_b["amps"][(i, t)]
                if amp_wa is not None and amp_wb is not None:
                    w_amp = amp_wa - amp_wb
                    
                lines = compute_combo_lines(u_amp, v_amp, w_amp, "美", "中", "日")
                day_dict["points"].append({"lines": lines})
                
            u_damp = v_damp = w_damp = None
            damp_ua = u_a["daily_amps"][i]
            damp_ub = u_b["daily_amps"][i]
            if damp_ua is not None and damp_ub is not None:
                u_damp = damp_ua - damp_ub
                
            damp_va = v_a["daily_amps"][i]
            damp_vb = v_b["daily_amps"][i]
            if damp_va is not None and damp_vb is not None:
                v_damp = damp_va - damp_vb
                
            damp_wa = w_a["daily_amps"][i]
            damp_wb = w_b["daily_amps"][i]
            if damp_wa is not None and damp_wb is not None:
                w_damp = damp_wa - damp_wb
                
            d_lines = compute_combo_lines(u_damp, v_damp, w_damp, "美", "中", "日")
            day_dict["daily"] = {"lines": d_lines}
            
            row_data["days"].append(day_dict)
            
        results.append(row_data)
        
    return results

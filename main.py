from contextlib import asynccontextmanager
from datetime import timedelta

from fastapi import FastAPI
from loguru import logger
from starlette.requests import Request
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from date_utils import current_app_date, resolve_friday_date
from db import init_db
from scheduler import StockDataScheduler
from service import query_weekly_amplitude, query_weekly_combo, query_weekly_bonds, query_weekly_bond_combo


@asynccontextmanager
async def lifespan(fast: FastAPI):
    # init_db 是 async 的，需要 await 才能真正执行
    await init_db()
    # 实例化调度器对象
    data_scheduler = StockDataScheduler()
    data_scheduler.start()
    logger.info("scheduler 启动")
    yield
    data_scheduler.stop()
    logger.info("scheduler 停止")


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def index(request: Request, friday_date: str = None):
    target_friday = resolve_friday_date(friday_date)
    current_date = current_app_date().strftime("%Y-%m-%d")
        
    weeks_data = []
    
    # 连续显示4周数据（最近的周排在最上面）
    for i in range(4):
        curr_friday_date = (target_friday - timedelta(days=i * 7)).strftime("%Y-%m-%d")
        data = await query_weekly_amplitude(curr_friday_date)
        combo_data = await query_weekly_combo(curr_friday_date)
        bonds_data = await query_weekly_bonds(curr_friday_date)
        bond_combo_data = await query_weekly_bond_combo(curr_friday_date)
        weeks_data.append({
            "friday_date": curr_friday_date,
            "data": data,
            "combo_data": combo_data,
            "bonds_data": bonds_data,
            "bond_combo_data": bond_combo_data
        })
    
    return templates.TemplateResponse(
        request=request, 
        name="index.html", 
        context={"request": request, "weeks_data": weeks_data, "current_date": current_date}
    )

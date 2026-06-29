import asyncio
import json
from pathlib import Path

import curl_cffi
from loguru import logger


class Api:
    def __init__(self):
        self.client = curl_cffi.AsyncSession(
            trust_env=False,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36"
            },
        )

    async def request(self, method: curl_cffi.requests.HttpMethod, url: str, **kwargs):
        res = await self.client.request(method=method, url=url, **kwargs)
        if res.status_code != 200:
            raise RuntimeError(f"请求失败: {url}, {res.status_code}, {res.text}")
        return res.json()

    async def mcn_finance_quotes(self):
        url = "https://assets.msn.cn/service/Finance/Quotes"
        params = {
            "apikey": "0QfOX3Vn51YCzitbLaRkTTBadtWpgTN8NZLW0C1SEM",
            "activityId": "69132974-e25b-4420-b669-43e5103891b5",
            "ocid": "finance-utils-peregrine",
            "cm": "zh-cn",
            "it": "web",
            "scn": "ANON",
            "ids": "avym77,av4yk2,av52z2,av4x6h,avys2w,avyn9c,ave1m7,ave6cw,a9j7bh,ah772w,adfh77,a33k6h,a6qja2,avyomw,avqrc7",
            "wrapodata": "false",
        }
        json_data = await self.request("GET", url, params=params)
        ret = []
        for data in json_data:
            one = data[0]
            symbol = one.get("friendlySymbol", one["symbol"])
            price = one['price']
            item = {
                "symbol": symbol,
                "price": price,
            }
            ret.append(item)
        return ret

    async def wallstreet_bonds(self, page: int = 1, size: int = 60):
        url = "https://api-ddc-wscn.awtmt.com/market/rank"
        params = {
            "market_type": "forexdata",
            "stk_type": "bond",
            "order_by": "none",
            "sort_field": "px_change_rate",
            "limit": size,
            "fields": "prod_name,prod_en_name,prod_code,symbol,last_px,px_change,px_change_rate,high_px,low_px,week_52_high,week_52_low,price_precision,update_time",
            "cursor": (page - 1) * size,
        }
        json_data = await self.request("GET", url, params=params)
        if json_data["code"] != 20000:
            raise RuntimeError(f'{json_data['code']}, {json_data["message"]}')
        data = json_data["data"]
        ret = []
        for one in data["candle"]:
            symbol = one[1]
            price = one[4]
            item = {
                "symbol": symbol,
                "price": price,
            }
            ret.append(item)

        return ret


async def main():
    api = Api()
    quotes = await api.mcn_finance_quotes()
    Path("mcn_finance_quotes_output.json").write_text(json.dumps(quotes, ensure_ascii=False), encoding="utf-8")

    bonds = await api.wallstreet_bonds()
    Path("wallstreet_bonds_output.json").write_text(json.dumps(bonds, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())

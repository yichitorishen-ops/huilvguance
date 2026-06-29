finance_map = {
    "USD/CNY": "美元/人民币",
    "CNY/JPY": "人民币/日元",
    "USD/JPY": "美元/日元",
    "JPY/RUB": "日元/俄罗斯卢布",
    "CNY/RUB": "人民币/俄罗斯卢布",
    "USD/RUB": "美元/俄罗斯卢布",
    "JPY/EUR": "日元/欧元",
    "RUB/EUR": "俄罗斯卢布/欧元",
    "CNY/EUR": "人民币/欧元",
    "USD/EUR": "美元/欧元",
}

bond_map = {
    "US2YR": "美2年",
    "US7YR": "美7年",
    "US10YR": "美10年",
    "US30YR": "美30年",
    "CN2YR": "中2年",
    "CN7YR": "中7年",
    "CN10YR": "中10年",
    "CN30YR": "中30年",
    "JP2YR": "日2年",
    "JP10YR": "日10年",
    "JP30YR": "日30年",
}

bond_diff = [
    ["US10YR", "CN10YR"],
    ["CN10YR", "CN2YR"],
    ["US10YR", "JP10YR"],
    ["CN10YR", "JP10YR"],
]

compose_list = [
    [
        {
            "symbol": "USD/CNY",
            "name": "美"
        },
        {
            "symbol": "CNY/JPY",
            "name": "中"
        },
        {
            "symbol": "USD/JPY",
            "name": "日"
        },
        "abc",
    ],
    [
        {
            "symbol": "USD/CNY",
            "name": "美"
        },
        {
            "symbol": "CNY/RUB",
            "name": "中"
        },
        {
            "symbol": "USD/RUB",
            "name": "卢"
        },
        "aef"
    ],
    [
        {
            "symbol": "USD/CNY",
            "name": "美"
        },
        {
            "symbol": "CNY/EUR",
            "name": "中"
        },
        {
            "symbol": "USD/EUR",
            "name": "欧"
        },
        "aij"
    ],
    [
        {
            "symbol": "CNY/JPY",
            "name": "中"
        },
        {
            "symbol": "JPY/RUB",
            "name": "日"
        },
        {
            "symbol": "CNY/RUB",
            "name": "卢"
        },
        "bde"
    ],
    [
        {
            "symbol": "CNY/JPY",
            "name": "中"
        },
        {
            "symbol": "JPY/EUR",
            "name": "日"
        },
        {
            "symbol": "CNY/EUR",
            "name": "欧"
        },
        "bgi"
    ],
    [
        {
            "symbol": "CNY/RUB",
            "name": "中"
        },
        {
            "symbol": "RUB/EUR",
            "name": "卢"
        },
        {
            "symbol": "CNY/EUR",
            "name": "欧"
        },
        "ehi"
    ],
    [
        {
            "symbol": "USD/JPY",
            "name": "美"
        },
        {
            "symbol": "JPY/RUB",
            "name": "日"
        },
        {
            "symbol": "USD/RUB",
            "name": "卢"
        },
        "cdf"
    ],
    [
        {
            "symbol": "USD/JPY",
            "name": "美"
        },
        {
            "symbol": "JPY/EUR",
            "name": "日"
        },
        {
            "symbol": "USD/EUR",
            "name": "欧"
        },
        "cgj"
    ],
    [
        {
            "symbol": "USD/RUB",
            "name": "美"
        },
        {
            "symbol": "RUB/EUR",
            "name": "卢"
        },
        {
            "symbol": "USD/EUR",
            "name": "欧"
        },
        "fhj"
    ],
]

bond_combo_price_list = [
    ("US10YR", "US2YR", "美10年-美2年"),
    ("CN10YR", "CN2YR", "中10年-中2年"),
    ("JP10YR", "JP2YR", "日10年-日2年"),
    ("US7YR", "US2YR", "美7年-美2年"),
    ("US10YR", "US7YR", "美10年-美7年"),
    ("US30YR", "US10YR", "美30年-美10年"),
    ("CN7YR", "CN2YR", "中7年-中2年"),
    ("CN10YR", "CN7YR", "中10年-中7年"),
    ("CN30YR", "CN10YR", "中30年-中10年"),
    ("JP30YR", "JP10YR", "日30年-日10年"),
]

bond_combo_amp_list = [
    ("US10YR", "CN10YR", "美10年-中10年"),
    ("CN10YR", "JP10YR", "中10年-日10年"),
    ("US10YR", "JP10YR", "美10年-日10年"),
    ("US2YR", "CN2YR", "美2年-中2年"),
    ("CN2YR", "JP2YR", "中2年-日2年"),
    ("US2YR", "JP2YR", "美2年-日2年"),
]

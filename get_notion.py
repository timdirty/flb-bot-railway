from notion_client import Client

# 初始化 Notion 用戶端
notion = Client(auth='ntn_c27641071407W6tF23uKOZVrOoQ0Dt5nINHvZJoSfRK6rJ')

# 目標資料庫 ID
database_id = "你的資料庫 ID"

# 查詢資料庫中的內容
response = notion.databases.query(
    **{
        "database_id": database_id,
    }
)

# 印出每一筆資料
for result in response["results"]:
    props = result["properties"]
    print("------")
    for key, val in props.items():
        print(f"{key} : {val.get(val['type'], {}).get('text', [{}])[0].get('plain_text', '') if val['type'] == 'title' else val.get(val['type'], '')}")
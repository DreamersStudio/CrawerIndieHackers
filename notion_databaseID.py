from notion_client import Client

notion = Client(auth="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")

# 获取所有数据库
response = notion.search(filter={"property": "object", "value": "database"})
for db in response["results"]:
    print(f"数据库名称: {db['title'][0]['plain_text']}")
    print(f"数据库 ID: {db['id']}\n")

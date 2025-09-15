from caldav import DAVClient

# Synology CalDAV 連線設定
url = 'https://funlearnbar.synology.me:9102/caldav/'
username = 'testacount'
password = 'testacount'

# 連線 CalDAV
client = DAVClient(url, username=username, password=password)
principal = client.principal()
calendars = principal.calendars()

if calendars:
    for calendar in calendars:
        print(f"📂 處理日曆: {calendar.name}")

        events = calendar.events()

        if not events:
            print(f"✅ 日曆 {calendar.name} 沒有事件，跳過。")
            continue

        for event in events:
            try:
                event.delete()
                print(f"🗑️ 已刪除事件: {event.url}")
            except Exception as e:
                print(f"❌ 刪除失敗: {str(e)}")

    print("✅ 所有日曆已清空！")
else:
    print("❌ 找不到任何日曆")

import os
import re
from datetime import datetime, timedelta

import pandas as pd
import pytz
from caldav import DAVClient

tz = pytz.timezone("Asia/Taipei")
weekday_dict = {
    0: "Ｍon",
    1: "Tue",
    2: "Wed",
    3: "Thu",
    4: "Fri",
    5: "Sat",
    6: "Sun",
}


def sep_name(text):
    if pd.isna(text):  # 如果是 NaN，直接回傳空 list
        return []
    return re.findall(r"([\u4e00-\u9fffA-Za-z]+) \(", text.upper())


# Synology CalDAV 設定
url = "https://funlearnbar.synology.me:9102/caldav/"
username = "testacount"
password = "testacount"

# 讀取 CSV
# df = pd.read_csv('20250708.csv', encoding='utf-8')
folder_path = "114-1課程規劃 2290a4c0ed84809eb9afca7fe276920d"

# 正規表達式模式
pattern_plan = re.compile(r".*課程規劃\s[\u4e00-\u9fa5a-zA-Z0-9]+_all\.csv")
pattern_schedule = re.compile(r".*_all\.csv$")  # 匹配所有 _all.csv 結尾的檔案

# 初始化變數
df_plan = None
schedule_files = []

# 遍歷資料夾中的檔案
for filename in os.listdir(folder_path):
    filepath = os.path.join(folder_path, filename)

    if pattern_plan.match(filename):
        df_plan = pd.read_csv(filepath, encoding="utf-8")
        print(f"✅ 讀取課程規劃檔案: {filename}")
    elif pattern_schedule.match(filename) and not pattern_plan.match(filename):
        schedule_files.append(filepath)
        print(f"✅ 找到展開課表檔案: {filename}")

print(f"📊 總共找到 {len(schedule_files)} 個展開課表檔案")

# 連線 CalDAV
client = DAVClient(url, username=username, password=password)
principal = client.principal()
calendars = principal.calendars()
calendar_map = {}

for cal in calendars:
    calendar_name = cal.name.upper()  # 直接用內建 name
    calendar_map[calendar_name] = cal

# 清空所有行事曆
print("🧹 開始清空所有行事曆...")
for calendar_name, calendar in calendar_map.items():
    try:
        events = calendar.events()
        event_count = 0
        for event in events:
            try:
                event.delete()
                event_count += 1
            except Exception as e:
                print(f"⚠️ 刪除事件失敗 ({calendar_name}): {e}")
        print(f"✅ 已清空 {calendar_name} 行事曆，刪除 {event_count} 個事件")
    except Exception as e:
        print(f"❌ 清空行事曆失敗 ({calendar_name}): {e}")

print("🎉 行事曆清空完成！\n")

if calendars and schedule_files:
    print("🚀 開始處理展開課表檔案...")
    
    for schedule_file in schedule_files:
        print(f"\n📁 處理檔案: {os.path.basename(schedule_file)}")
        
        try:
            df_schedule = pd.read_csv(schedule_file, encoding="utf-8")
            
            for index, row in df_schedule.iterrows():
                # 跳過空行
                if pd.isna(row["課程名稱"]) or row["課程名稱"] == "":
                    continue
                    
                event_title = row["課程名稱"]
                raw_time = row["起始日期"]
                class_id = int(row["課別"])
                
                # 解析時間格式
                time_match = re.match(r"(\d{4})年(\d{1,2})月(\d{1,2})日 (\d{1,2}):(\d{2}) \(GMT\+8\) → (\d{1,2}):(\d{2})", str(raw_time))
                if not time_match:
                    print(f"⚠️ 無法解析時間格式: {raw_time}")
                    continue
                    
                year, month, day, start_hour, start_min, end_hour, end_min = time_match.groups()
                start_time = f"{start_hour}:{start_min}"
                end_time = f"{end_hour}:{end_min}"

                teacher_name_list = sep_name(row["講師"])
                TA_name_list = sep_name(row["助教"])
                
                # 組合成 datetime 格式
                start_datetime = tz.localize(
                    datetime.strptime(f"{year}-{month}-{day} {start_time}", "%Y-%m-%d %H:%M")
                )
                end_datetime = tz.localize(
                    datetime.strptime(f"{year}-{month}-{day} {end_time}", "%Y-%m-%d %H:%M")
                )

                class_name = row["課程名稱"]
                class_cl = row["上課位置"]
                class_address = row["上課地址"]
                lesson_plan = row.get("SPM教案 ", "") or row.get("教案", "") or ""
                
                # 建立事件資料
                event_data = f"""BEGIN:VCALENDAR
VERSION:2.0 
BEGIN:VEVENT
UID:{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}@example.com
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART;TZID=Asia/Taipei:{start_datetime.strftime('%Y%m%dT%H%M%SZ')}
DTEND;TZID=Asia/Taipei:{end_datetime.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{event_title} 第{class_id}週
DESCRIPTION:時間: {start_datetime.strftime('%Y%m%d')} {start_time}-{end_time} 班級:{class_name} 講師: {row['講師']} 助教: {row['助教']} 教案: {lesson_plan}
LOCATION:{class_address}
END:VEVENT
END:VCALENDAR
"""
                
                # 處理老師行事曆
                if teacher_name_list:
                    for teacher_name in teacher_name_list:
                        if teacher_name in calendar_map:
                            calendar_map[teacher_name].add_event(event_data)
                            print(f"✅ 已新增事件: {teacher_name} {event_title} 第{class_id}週 {start_datetime}")
                        else:
                            print(f"⚠️ 找不到講師行事曆: {teacher_name}")
                else:
                    print(f"⏩ 沒有老師需要新增，跳過。")

                # 處理 TA 行事曆
                if TA_name_list:
                    for TA_name in TA_name_list:
                        if TA_name in calendar_map:
                            calendar_map[TA_name].add_event(event_data)
                            print(f"✅ 已新增事件: {TA_name} {event_title} 第{class_id}週 {start_datetime}")
                        else:
                            print(f"⚠️ 找不到助教行事曆: {TA_name}")
                else:
                    print(f"⏩ 沒有 TA 需要新增，跳過。")
                    
        except Exception as e:
            print(f"❌ 處理檔案失敗 {os.path.basename(schedule_file)}: {e}")
            continue
else:
    print("❌ 找不到日曆")

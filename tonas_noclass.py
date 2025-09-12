import os
import re
from datetime import datetime, timedelta

import pandas as pd
import pytz
from caldav import DAVClient

tz = pytz.timezone("Asia/Taipei")

# 映射：週一=0 ... 週日=6
weekday_char2idx = {
    "一": 0,
    "二": 1,
    "三": 2,
    "四": 3,
    "五": 4,
    "六": 5,
    "日": 6,
    "天": 6,
}


def sep_name(text):
    if pd.isna(text):
        return []
    return re.findall(r"([\u4e00-\u9fffA-Za-z]+) \(", str(text).upper())


# === 新增：解析「星期」欄位，可含多天（, 、 ， 及空白分隔）===
def parse_weekdays(cell: str):
    if not isinstance(cell, str):
        return []
    chars = re.findall(r"[一二三四五六日天]", cell)
    return [weekday_char2idx[c] for c in chars if c in weekday_char2idx]


# === 新增：解析時間區間（例如 16:30-17:30）===
def parse_time_range(s: str):
    m = re.search(r"([0-2]?\d:[0-5]\d)\s*-\s*([0-2]?\d:[0-5]\d)", str(s))
    if not m:
        return None, None
    st = datetime.strptime(m.group(1), "%H:%M").time()
    et = datetime.strptime(m.group(2), "%H:%M").time()
    return st, et


# === 新增：解析起始日期（支援 2025/07/19、2025-07-19、或 2025年7月19日）===
def parse_start_date(s: str):
    s = str(s).strip()
    for fmt in ("%Y/%m/%d", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    m = re.search(r"(\d{4})年(\d{1,2})月(\d{1,2})日", s)
    if m:
        y, mth, d = map(int, m.groups())
        return datetime(y, mth, d).date()
    return None


# === 新增：從 base_date（含當日）往後取得第一個指定星期 ===
def next_weekday_on_or_after(base_date, target_wd: int):
    delta = (target_wd - base_date.weekday()) % 7
    return base_date + timedelta(days=delta)


# ====== 你的 CalDAV、CSV 掃描部分維持不變（略） ======
url = "https://funlearnbar.synology.me:9102/caldav/"
username = "testacount"
password = "testacount"

folder_path = "114-1課程規劃 2290a4c0ed84809eb9afca7fe276920d"
pattern_plan = re.compile(r".*課程規劃\s[\u4e00-\u9fa5a-zA-Z0-9]+_all\.csv")

df_plan = None
for filename in os.listdir(folder_path):
    if pattern_plan.match(filename):
        df_plan = pd.read_csv(os.path.join(folder_path, filename), encoding="utf-8")
        print(f"✅ 讀取課程規劃檔案: {filename}")
        break

client = DAVClient(url, username=username, password=password)
principal = client.principal()
calendars = principal.calendars()
calendar_map = {cal.name.upper(): cal for cal in calendars}

# ====== 主要迭代：支援一週多天 ======
if calendars and df_plan is not None:
    WEEKS = 16  # 展開週數
    for index, row in df_plan.iterrows():
        event_title = row["課程名稱"]
        class_name = row["課程內容"]
        class_cl = row["上課位置"]
        class_addr = row["上課地址"]

        # 解析多個星期與時間區間
        weekdays = parse_weekdays(row["星期"])  # 例：['二, 四'] -> [1, 3]
        start_t, end_t = parse_time_range(row["時間"])  # 例："16:30-17:30"
        base_date = parse_start_date(row.get("起始日期", ""))

        if not weekdays or not start_t or not end_t or not base_date:
            print(f"⚠️ 第 {index} 列資料不足，跳過（weekdays/time/base_date）。")
            continue

        # 老師/助教
        teacher_name_list = sep_name(row["講師"])
        TA_name_list = sep_name(row["助教"])

        for s_idx, wd in enumerate(weekdays, start=1):
            # 找到此星期的第一堂課日期
            first_date = next_weekday_on_or_after(base_date, wd)

            # 該星期的第一堂 start/end datetime
            start_dt0 = tz.localize(datetime.combine(first_date, start_t))
            end_dt0 = tz.localize(datetime.combine(first_date, end_t))

            for w in range(WEEKS):
                final_start = start_dt0 + timedelta(days=7 * w)
                final_end = end_dt0 + timedelta(days=7 * w)

                event_data = f"""BEGIN:VCALENDAR
VERSION:2.0
BEGIN:VEVENT
UID:{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}@example.com
DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}
DTSTART;TZID=Asia/Taipei:{final_start.strftime('%Y%m%dT%H%M%SZ')}
DTEND;TZID=Asia/Taipei:{final_end.strftime('%Y%m%dT%H%M%SZ')}
SUMMARY:{event_title} {class_name} 週{w+1}   
DESCRIPTION:時間: {final_start.strftime('%Y%m%d')} {start_t.strftime('%H:%M')}-{end_t.strftime('%H:%M')} 班級:{class_name}{class_cl} 講師: {row['講師']} 助教: {row['助教']} 教案: 暫無
LOCATION:{class_addr}
END:VEVENT
END:VCALENDAR
"""

                # 老師行事曆
                if teacher_name_list:  # 有抓到講師名字才進行
                    for tname in teacher_name_list:
                        key = tname.upper()
                        if key in calendar_map:
                            calendar_map[key].add_event(event_data)
                            print(
                                f"✅ 老師 {tname} 已新增 {event_title}：{final_start}"
                            )
                        else:
                            print(f"❗ 找不到老師行事曆：{tname}")
                else:
                    print(f"⏩ 第 {index} 列講師為空，略過老師行事曆")

                # 助行情事曆
                if TA_name_list:
                    for aname in TA_name_list:
                        key = aname.upper()
                        if key in calendar_map:
                            calendar_map[key].add_event(event_data)
                            print(
                                f"✅ 助教 {aname} 已新增 {event_title}：{final_start}"
                            )
                        else:
                            print(f"❗ 找不到助行情事曆：{aname}")
else:
    print("❌ 找不到日曆或 CSV")

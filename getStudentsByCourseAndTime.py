import requests
import json

API_URL = 'https://script.google.com/macros/s/AKfycbxfj5fwNIc8ncbqkOm763yo6o06wYPHm2nbfd_1yLkHlakoS9FtYfYJhvGCaiAYh_vjIQ/dev'

def post_action(action, payload=None):
    """共用函數：送出 action 請求"""
    data = {"action": action}
    if payload:
        data.update(payload)
    try:
        response = requests.post(API_URL, headers={"Content-Type": "application/json"}, data=json.dumps(data))
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        return None

def get_courses():
    """取得課程清單"""
    result = post_action("getCoursesForSelect")
    if result and result.get("success"):
        return result["courses"]
    return []

def get_times_by_course(course):
    """取得指定課程的時段清單"""
    result = post_action("getTimesByCourse", {"course": course})
    if result and result.get("success"):
        return result["times"]
    return []

def get_students_by_course_and_time(course, time):
    """取得指定課程與時段的學生名單"""
    result = post_action("getStudentsByCourseAndTime", {"course": course, "time": time})
    if result and result.get("success"):
        students = result.get("students", [])
        if students:
            return students
        else:
            print(f"⚠️ 課程「{course}」時段「{time}」目前沒有學生")
            return []
    else:
        print(f"❌ 查詢失敗：{result.get('error', '未知錯誤') if result else 'API 呼叫失敗'}")
        return []

def choose_from_list(options, prompt):
    """讓使用者從選項清單中選擇"""
    print(f"\n🔘 {prompt}")
    for i, option in enumerate(options, 1):
        print(f"{i}. {option}")
    while True:
        choice = input("請輸入編號：")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            return options[int(choice) - 1]
        else:
            print("❌ 請輸入有效的選項編號")

def interactive_query():
    """互動式查詢課程＋時段的學生清單"""
    print("🎓 查詢課程＋時段的學生清單")
    print("=" * 40)

    courses = get_courses()
    if not courses:
        print("❌ 無法取得課程清單")
        return
    selected_course = choose_from_list(courses, "請選擇課程名稱")

    times = get_times_by_course(selected_course)
    if not times:
        print("❌ 無法取得上課時間")
        return
    selected_time = choose_from_list(times, f"請選擇「{selected_course}」的上課時間")

    students = get_students_by_course_and_time(selected_course, selected_time)
    if students is None:
        print("❌ 無法取得學生名單")
        return

    print(f"\n📋 課程：{selected_course}")
    print(f"🕒 時段：{selected_time}")
    print(f"👥 學生名單（共 {len(students)} 人）：")
    print("-" * 40)
    for s in students:
        print(f"👤 {s}")
    print("-" * 40)

if __name__ == "__main__":
    interactive_query()
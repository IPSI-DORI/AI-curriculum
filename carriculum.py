from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import pandas as pd
import time


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 창 띄우기 싫으면 주석 해제
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def get_intro(driver):
    intro_data = {}
    try:
        title = driver.find_element(By.CSS_SELECTOR, ".tit_wrap .tit").text
        teacher = driver.find_element(By.CSS_SELECTOR, ".name").text
        description = driver.find_element(By.CSS_SELECTOR, ".cont_para").text
        intro_data = {"title": title, "teacher": teacher, "description": description}
    except Exception as e:
        print(f"Intro 추출 중 에러 발생: {e}")
    return intro_data


def get_lectures(driver):
    lectures = []
    try:
        lecture_items = driver.find_elements(By.CSS_SELECTOR, "div.board_list2 ul li.tbody")
        for item in lecture_items:
            try:
                title = item.find_element(By.CSS_SELECTOR, "p.title").text.strip()
                info = item.find_element(By.CSS_SELECTOR, "p.info").text.strip()
                lectures.append({
                    "title": title,
                    "info": info
                })
            except Exception as e:
                print(f"개별 강의 추출 에러: {e}")
    except Exception as e:
        print(f"Lecture 전체 추출 에러: {e}")
    return lectures


def get_review_count(driver):
    try:
        count_text = driver.find_element(By.CSS_SELECTOR, ".board_head.type1 .count_area .tot em").text
        count = int(count_text.replace(",", "").strip())
        return count
    except Exception as e:
        print(f"Review count 추출 중 에러 발생: {e}")
        return 0


def scrape_course(driver, course_id):
    base_url = f"https://www.ebsi.co.kr/ebs/lms/lmsx/retrieveSbjtDtl.ebs?courseId={course_id}"

    course_data = {"course_id": course_id}

    driver.get(base_url)
    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".tit_wrap .tit"))
        )
        time.sleep(1)
        course_data.update(get_intro(driver))
    except TimeoutException:
        print(f"[Timeout] Intro 탭 로딩 실패 (course_id: {course_id})")
        driver.save_screenshot(f"error_{course_id}_intro.png")
        return course_data

    # ===== Lecture 탭 클릭 =====
    try:
        lecture_tab = driver.find_element(By.CSS_SELECTOR, "a[href='#lecture']")
        lecture_tab.click()
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.board_list2"))
        )
        time.sleep(1)
        course_data["lectures"] = get_lectures(driver)
    except TimeoutException:
        print(f"[Timeout] Lecture 탭 로딩 실패 (course_id: {course_id})")
        course_data["lectures"] = []
    except Exception as e:
        print(f"[Error] Lecture 탭 클릭 실패: {e}")
        course_data["lectures"] = []

    # ===== Epilogue 탭 클릭 =====
    try:
        epilogue_tab = driver.find_element(By.CSS_SELECTOR, "a[href='#epilogue']")
        epilogue_tab.click()
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".board_head.type1 .count_area .tot em"))
        )
        time.sleep(1)
        course_data["reviews"] = get_review_count(driver)
    except TimeoutException:
        print(f"[Timeout] Epilogue 탭 로딩 실패 (course_id: {course_id})")
        course_data["reviews"] = []
    except Exception as e:
        print(f"[Error] Epilogue 탭 클릭 실패: {e}")
        course_data["reviews"] = []

    return course_data

def main():
    course_ids = [
        "S20240000896",
    ]

    driver = create_driver()

    all_courses = []  # 전체 course 메타 데이터 모을 리스트
    all_lectures = []  # 전체 강의 데이터 모을 리스트

    for course_id in course_ids:
        data = scrape_course(driver, course_id)

        # course 메타 데이터
        course_meta = {
            "course_id": data["course_id"],
            "title": data.get("title", ""),
            "teacher": data.get("teacher", ""),
            "description": data.get("description", ""),
            "reviews": data.get("reviews", 0)
        }
        all_courses.append(course_meta)

        # lectures 데이터
        lectures = data.get("lectures", [])
        for lecture in lectures:
            lecture_entry = {
                "course_id": data["course_id"],  # 어떤 course에 속하는지 알기 위해
                "title": lecture.get("title", ""),
                "info": lecture.get("info", "")
            }
            all_lectures.append(lecture_entry)

        print(f"[완료] {course_id}")

    driver.quit()

    # 각각 DataFrame 만들기
    courses_df = pd.DataFrame(all_courses)
    lectures_df = pd.DataFrame(all_lectures)

    # CSV 저장
    courses_df.to_csv("courses.csv", index=False, encoding="utf-8-sig")
    lectures_df.to_csv("lectures.csv", index=False, encoding="utf-8-sig")

    print("✅ CSV 파일 저장 완료: courses.csv / lectures.csv")

if __name__ == "__main__":
    main()
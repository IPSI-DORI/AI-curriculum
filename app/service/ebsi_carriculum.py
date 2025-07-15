from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from app.utils.s3_utils import upload_to_s3
import pandas as pd
import shutil
import os
import time
import json


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
        # intro 정보 추출
        cont_group = driver.find_elements(By.CLASS_NAME, "cont_group")

        title = driver.find_element(
            By.CSS_SELECTOR,
            "body > div.wrap > section > div > div.content > form:nth-child(13) > div.all_lecture_info > div.all_lecture_items > div.cont_wrap > div.tit_wrap > h2",
        ).text
        teachers = driver.find_elements(By.CSS_SELECTOR, ".name strong")

        if len(teachers) > 1:
            # teacher = teachers[2].text.strip() + "," + teachers[3].text.strip()
            teacher = teachers[1].text.strip()
        else:
            teacher = teachers[0].text.strip()
        dds = driver.find_elements(By.CSS_SELECTOR, "dl.cont_info2 dd")
        dts = driver.find_elements(By.CSS_SELECTOR, "dl.cont_info2 dt")
        subject = dds[0].text.strip()
        grade = dds[3].text.strip()
        dificulty_level = dds[2].text.strip()
        if len(cont_group) > 3:
            description = (
                driver.find_element(
                    By.CSS_SELECTOR,
                    "#gotoTab > div > div > div:nth-child(2) > p.cont_tit",
                ).text
                + ":"
                + driver.find_element(
                    By.CSS_SELECTOR,
                    "#gotoTab > div > div > div:nth-child(2) > p.cont_para",
                ).text
                + "\n"
                + driver.find_element(
                    By.CSS_SELECTOR,
                    "#gotoTab > div > div > div:nth-child(3) > p.cont_tit",
                ).text
                + ":"
                + driver.find_element(
                    By.CSS_SELECTOR,
                    "#gotoTab > div > div > div:nth-child(3) > p.cont_para",
                ).text
            )
        else:
            description = (
                dts[1].text.strip()
                + ":"
                + dds[1].text.strip()
                + "\n"
                + dts[2].text.strip()
                + ":"
                + dds[2].text.strip()
            )
            print("single info.")
        intro_data = {
            "title": title,
            "teacher": teacher,
            "subject": subject,
            "description": description,
            "grade": grade,
            "platform": "ebsi",
            "is_paid": False,
            "price": 0,
            "dificulty_level": dificulty_level,
        }
    except Exception as e:
        print(f"Intro 추출 중 에러 발생: {e}")
    return intro_data


# gotoTab > div > div > div:nth-child(2)


def get_lectures(driver):
    lectures = []
    try:
        lecture_items = driver.find_elements(
            By.CSS_SELECTOR, "div.board_list2 ul li.tbody"
        )
        for item in lecture_items:
            try:
                title = item.find_element(By.CSS_SELECTOR, "p.title").text.strip()
                info = item.find_element(By.CSS_SELECTOR, "p.info").text.strip()
                lectures.append({"title": title, "info": info})
            except Exception as e:
                print(f"개별 강의 추출 에러: {e}")
    except Exception as e:
        print(f"Lecture 전체 추출 에러: {e}")
    return lectures


def get_review_count(driver):
    try:
        count_text = driver.find_element(
            By.CSS_SELECTOR, ".board_head.type1 .count_area .tot em"
        ).text
        count = int(count_text.replace(",", "").strip())
        return count
    except Exception as e:
        print(f"Review count 추출 중 에러 발생: {e}")
        return 0


def scrape_course(driver, course_id):
    base_url = (
        f"https://www.ebsi.co.kr/ebs/lms/lmsx/retrieveSbjtDtl.ebs?courseId={course_id}"
    )

    course_data = {"course_id": course_id}

    course_data["url"] = base_url
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
        lecture_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href='#lecture']"))
        )
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
        # "Epilogue" 탭이 존재하고 클릭 가능한지 확인
        epilogue_tab = driver.find_element(By.CSS_SELECTOR, "a[href='#epilogue']")
        driver.execute_script("arguments[0].click();", epilogue_tab)
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".board_head.type1 .count_area .tot em")
            )
        )
        time.sleep(1)
        course_data["reviews"] = get_review_count(driver)
    except (TimeoutException, NoSuchElementException):
        print(f"[Info] Epilogue 탭이 없거나 클릭할 수 없습니다 (course_id: {course_id})")
        course_data["reviews"] = []
    except Exception as e:
        print(f"[Error] Epilogue 탭 처리 중 예외 발생: {e}")
        course_data["reviews"] = []

    return course_data

def crawling_ebs():
    try:
        with open("ebs_urls.json", encoding="utf-8") as f:
            courses_items = json.load(f)

        driver = create_driver()

        # 대과목별 데이터 저장
        subject_course_map = {}
        subject_lecture_map = {}

        for item in courses_items:
            course_id = item["course_id"]
            subject_full = item["subject"]

            # 대과목 추출 (예: "국어-문학" → "국어")
            major_subject = subject_full.split("-")[0]

            # 크롤링
            data = scrape_course(driver, course_id)

            # course 데이터
            course_meta = {
                "course_id": course_id,
                "title": data.get("title", ""),
                "teacher": data.get("teacher", ""),
                "subject": subject_full,
                "description": data.get("description", ""),
                "reviews": data.get("reviews", 0),
                "grade": data.get("grade", ""),
                "platform": data.get("platform", ""),
                "is_paid": data.get("is_paid", False),
                "price": data.get("price", 0),
                "difficulty_level": data.get("dificulty_level", ""),
                "url": data.get("url", "")
            }
            subject_course_map.setdefault(major_subject, []).append(course_meta)

            # lecture 데이터
            lectures = data.get("lectures", [])
            for lecture in lectures:
                lecture_entry = {
                    "course_id": course_id,
                    "title": lecture.get("title", ""),
                    "info": lecture.get("info", "")
                }
                subject_lecture_map.setdefault(major_subject, []).append(lecture_entry)

            print(f"[완료] {course_id} ({subject_full})")

        driver.quit()

        # 과목별 CSV 저장 및 S3 업로드
        for subject, course_list in subject_course_map.items():
            courses_df = pd.DataFrame(course_list)
            lectures_df = pd.DataFrame(subject_lecture_map.get(subject, []))

            courses_filename = f"{subject}_courses.csv"
            lectures_filename = f"{subject}_lectures.csv"

            # S3 업로드만 수행
            upload_to_s3(courses_df, courses_filename)
            upload_to_s3(lectures_df, lectures_filename)

            print(f"✅ S3 업로드 완료: {subject}")

        return "🎉 모든 과목별 S3 업로드 완료"
    except Exception as e:
        return f"❌ Error occurred: {str(e)}"

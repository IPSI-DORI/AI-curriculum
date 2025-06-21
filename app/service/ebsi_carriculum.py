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
            "platform": "EBS",
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
        courses_dir = "../../courses.csv"
        lectures_dir = "../../lectures.csv"

        if os.path.exists(courses_dir):
            shutil.rmtree(courses_dir)
        if os.path.exists(lectures_dir):
            shutil.rmtree(lectures_dir)
        
        course_ids = [
            # 국어
            # 국어 - 문학
            "S20240000899",
            "S20250000002",
            "S20240000896",
            "S20250000032",
            # 국어 - 독서
            "S20250000033",
            # 국어 - 화작
            "S20240000902",
            "S20250000034",
            # 국어 - 언어와 매체
            "S20240000904",
            "S20250000035",
            # 수학
            # 수학 - 수학1
            "S20240000908",
            "S20240000909",
            # 수학 - 확통
            "S20240000912",
            "S20240000021",
            "S20250000038",
            # 수학 - 수학2
            "S20240000910",
            # 수학 - 1 + 2
            "S20240000906",
            "S20250000036",
            # 수학 - 미적분
            "S20250000037",
            # 수학 - 기하
            "S20240000916",
            # 영어
            "S20240000918",
            "S20240000919",
            "S20240000920",
            "S20240000923",
            "S20240000787",
            "S20240000924",
            "S20240000925",
            "S20250000039",
            "S20250000040",
            # 한국사
            "S20250000001",
            "S20240000926",
            "S20240000927",
            "S20240000791",
            "S20240000835",
            "S20240000852",
            "S20210001278",
            "S20250000041",
            # 생활과 윤리
            "S20240000928",
            "S20250000045",
            # 윤리와 사상
            "S20240000931",
            "S20240000929",
            "S20250000048",
            # 한국지리
            "S20240000933",
            "S20250000050",
            # 동아시아사
            "S20240000938",
            "S20250000043",
            # 세계사
            "S20250000046",
            # 세계지리
            "S20250000047",
            # 사회문화
            "S20240000794",
            "S20240000945",
            "S20250000044",
            # 생명과학1
            "S20240000958",
            "S20250000053",
            "S20240000960",
            "S20240000959",
            # 생명과학2
            "S20250000054",
            # 화학1
            "S20240000953",
            "S20250000057",
            # 화학2
            "S20250000058",
            # 지구과학1
            "S20240000965",
            "S20240000859",
            "S20250000055",
            "S20240000963",
            # 지구과학2
            "S20250000056",
            # 물리1
            "S20250000051",
            # 물리2
            "S20250000052",
        ]

        driver = create_driver()

        all_courses = []  # 전체 course 메타 데이터 모을 리스트
        all_lectures = []  # 전체 강의 데이터 모을 리스트

        for course_id in course_ids:
            if course_id == "S20240000859":
                print("skip S20240000859")
            data = scrape_course(driver, course_id)

            # course 메타 데이터
            course_meta = {
                "course_id": data["course_id"],
                "title": data.get("title", ""),
                "teacher": data.get("teacher", ""),
                "subject": data.get("subject", ""),
                "description": data.get("description", ""),
                "reviews": data.get("reviews", 0),
                "grade": data.get("grade", ""),
                "platform": data.get("platform", ""),
                "is_paid": data.get("is_paid", False),
                "price": data.get("price", 0),
                "dificulty_level": data.get("dificulty_level", ""),
                "url": data.get("url", ""),
            }
            all_courses.append(course_meta)

            # lectures 데이터
            lectures = data.get("lectures", [])
            for lecture in lectures:
                lecture_entry = {
                    "course_id": data["course_id"],  # 어떤 course에 속하는지 알기 위해
                    "title": lecture.get("title", ""),
                    "info": lecture.get("info", ""),
                }
                all_lectures.append(lecture_entry)

            print(f"[완료] {course_id}")

        driver.quit()

        # 각각 DataFrame 만들기
        courses_df = pd.DataFrame(all_courses)
        lectures_df = pd.DataFrame(all_lectures)

        # CSV 저장
        # courses_df.to_csv("courses.csv", index=False, encoding="utf-8-sig")
        # lectures_df.to_csv("lectures.csv", index=False, encoding="utf-8-sig")
        
        upload_to_s3(courses_df, "courses.csv")
        upload_to_s3(lectures_df, "lectures.csv")

        return("✅ CSV 파일 저장 완료: courses.csv / lectures.csv")
    except Exception as e:
        return f"Error occurred: {str(e)}"
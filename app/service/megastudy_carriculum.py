from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import pandas as pd
import shutil
import os
import re
from selenium.webdriver.support import expected_conditions as EC
import time


def create_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)
    return driver


def scrape_megastudy_course(driver, url):
    data = {
        "url": url,
        "platform": "megastudy",
        "is_paid": True,
        "price": None,
        "lectures": [],  # 대부분 없거나 접근 불가
    }

    driver.get(url)

    try:
        # 강의명
        title = driver.find_element(By.CSS_SELECTOR, "#wrap_2014 > div.column_main > div.column_right > div.l_lst2018 > div.bx_detail > div.bx_detail--infos > div > p.lstedu_bookinfo--tit").text.strip()
        data["title"] = title
    except:
        data["title"] = ""

    try:
        # 강사명
        teacher_subject = driver.find_element(By.CSS_SELECTOR, "#wrap_2014 > div.column_main > div.column_right > div.l_lst2018 > div.bx_detail > div.bx_detail--infos > div > p.lstedu_bookinfo--teacher > strong > a").text.strip().split(" ")
        match = re.compile('\[([^]]+)\]')
        subject = match.findall(teacher_subject[0])
        teacher = teacher_subject[1]
        data["teacher"] = teacher
        data["subject"] = subject[0]
    except:
        data["teacher"] = ""
        data["subject"] = ""

    try:
        # 수강 대상 및 과목 정보 (타겟/과목명/학년 등 포함됨)
        info_area = driver.find_element(By.CSS_SELECTOR, "#wrap_2014 > div.column_main > div.column_right > div.l_lst2018 > div.bx_detail > div.bx_detail--infos > div > ul > li:nth-child(1) > dl:nth-child(1) > dd").text.strip()
        data["grade"] = info_area
    except:
        data["grade"] = ""

    try:
        # 강좌 설명
        description = driver.find_element(By.CSS_SELECTOR, ".editArea").text.strip()
        data["description"] = description
    except:
        data["description"] = ""

    try:
        # 가격 정보
        price_text = driver.find_element(By.CSS_SELECTOR, ".lstedu_bxitem .bx_price--info").text
        price = int(price_text.replace(",", "").replace("원", "").strip())
        data["price"] = price
        data["is_paid"] = price > 0
    except:
        data["price"] = None
        data["is_paid"] = True  # 메가스터디는 대부분 유료

    try:
        # 가격 정보
        lectures_row = driver.find_elements(By.CSS_SELECTOR, "#scrollTab2 .tb_char_opt tbody tr")
        
        for row in lectures_row:
            lecture_data = {}
            try:
                # 여기서 부터 다시 시작, 시간 정보, 제목 제대로 나누게 끔 만들기기
                data_split = row.text.split("\n")
                lecture_data["title"] = data_split[0].strip()  # 강의 제목
                lecture_data["info"] = data_split[1].strip() if len(data_split) > 1 else ""  # 강의 정보
                print(lecture_data["title"])
                print(lecture_data["info"])
                data["lectures"].append(lecture_data)
            except:
                continue
        
    except:
        data["price"] = None
        data["is_paid"] = True  # 메가스터디는 대부분 유료
        
    return data


def main(): 
    all_courses = []  # 전체 course 메타 데이터 모을 리스트
    all_lectures = []  # 전체 강의 데이터 모을 리스트
    
    courses_dir = "../../courses_mega.csv"
    lectures_dir = "../../lectures_mega.csv"

    if os.path.exists(courses_dir):
        shutil.rmtree(courses_dir)
    if os.path.exists(lectures_dir):
        shutil.rmtree(lectures_dir)
    
    urls = [
        "https://www.megastudy.net/lecmain/mains/chr_detail/lecture_detailview.asp?CHR_CD=56856&MAKE_FLG=2&tec_cd=megabori",
        "https://www.megastudy.net/lecmain/mains/chr_detail/lecture_detailview.asp?CHR_CD=56506&MAKE_FLG=2&tec_cd=goodwill96",
        "https://www.megastudy.net/lecmain/mains/chr_detail/lecture_detailview.asp?CHR_CD=54613&MAKE_FLG=1&tec_cd=woojinmath",
    ]

    driver = create_driver()

    for url in urls:
        match = re.search(r'CHR_CD=(\d+)', url)
        course_id = match.group(1)
        data = scrape_megastudy_course(driver, url)
        
        # course 메타 데이터
        course_meta = {
            "course_id": course_id,
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
        }
        all_courses.append(course_meta)

        # lectures 데이터
        lectures = data.get("lectures", [])
        for lecture in lectures:
            lecture_entry = {
                "course_id": course_id,  # 어떤 course에 속하는지 알기 위해
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
    courses_df.to_csv("courses_mega.csv", index=False, encoding="utf-8-sig")
    lectures_df.to_csv("lectures_mega.csv", index=False, encoding="utf-8-sig")

if __name__ == "__main__":
    main()

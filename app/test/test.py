from selenium import webdriver
from selenium.webdriver.common.by import By
import time

# Selenium WebDriver 설정
options = webdriver.ChromeOptions()
options.add_argument("--headless")  # 창을 띄우지 않고 실행
driver = webdriver.Chrome(options=options)

# EBSi 강좌 페이지 접속
course_id = "S20240000899"
url = f"https://www.ebsi.co.kr/ebs/lms/lmsx/retrieveSbjtDtl.ebs?courseId={course_id}"
driver.get(url)

try:
    # "Epilogue" 탭 요소 찾기
    epilogue_tab = driver.find_element(By.CSS_SELECTOR, "a[href='#epilogue']")

    # JavaScript를 사용하여 클릭
    driver.execute_script("arguments[0].click();", epilogue_tab)

    # Epilogue 콘텐츠가 로드될 때까지 대기
    time.sleep(2)  # 필요에 따라 조정

    # Epilogue 콘텐츠 출력 (예: 리뷰 수)
    review_count = driver.find_element(By.CSS_SELECTOR, ".board_head.type1 .count_area .tot em").text
    print(f"리뷰 수: {review_count}")
except Exception as e:
    print(f"오류 발생: {e}")

# 브라우저 종료
driver.quit()

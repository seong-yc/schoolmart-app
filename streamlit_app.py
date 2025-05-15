# streamlit_app.py
import streamlit as st
import pandas as pd
import zipfile
import requests
from io import BytesIO
from bs4 import BeautifulSoup
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from dotenv import load_dotenv

# --------- 환경변수 로드 ---------
load_dotenv()
DOMEGGOOK_ID = os.getenv("DOMEGGOOK_ID")
DOMEGGOOK_PW = os.getenv("DOMEGGOOK_PW")

# --------- 크롤링 함수 ---------
def get_product_info_from_url(url: str) -> Dict[str, str]:
    try:
        # Selenium 설정
        options = Options()
        # options.add_argument('--headless')  # 디버깅 시 주석 처리하면 크롬 창이 뜸
        options.add_argument('--disable-gpu')
        options.add_argument('--no-sandbox')
        options.add_argument('--window-size=1920x1080')  # 안정적인 로딩을 위해 권장
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

        # 로그인 처리
        driver.get("https://domeggook.com/login")
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "user_id")))
        driver.find_element(By.ID, "user_id").send_keys(DOMEGGOOK_ID)
        driver.find_element(By.ID, "user_pw").send_keys(DOMEGGOOK_PW + Keys.RETURN)
        time.sleep(2)

        # 상품 페이지 접속
        driver.get(url)
        time.sleep(2)
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")

        def extract_text(selector, attr=None):
            tag = soup.select_one(selector)
            if tag:
                return tag.get(attr) if attr else tag.get_text(strip=True)
            return "N/A"

        product_info = {
            "상품명": extract_text("meta[property='og:title']", attr="content"),
            "대표 이미지 URL": extract_text("meta[property='og:image']", attr="content"),
            "상품설명 HTML": str(soup.find("div", {"id": "tabPageDetail"})) or "N/A",
            "공급사명": "N/A",
            "원산지": "N/A",
            "배송방법": "N/A",
            "배송금액": "N/A",
            "수량기준": "N/A",
            "단가": "N/A",
            "상품URL": url,
            "옵션목록": []
        }

        # 테이블 정보 추출
        tables = soup.find_all("table")
        for table in tables:
            for row in table.find_all("tr"):
                cells = row.find_all(["th", "td"])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if "공급사명" in key:
                        product_info["공급사명"] = value
                    elif "원산지" in key:
                        product_info["원산지"] = value
                    elif "배송방법" in key:
                        product_info["배송방법"] = value
                    elif "배송금액" in key:
                        product_info["배송금액"] = value
                    elif "수량" in key:
                        product_info["수량기준"] = key
                        product_info["단가"] = value

        # 옵션 정보 추출
        option_table = soup.find("table", {"class": "table_item_option"})
        if option_table:
            for row in option_table.find_all("tr"):
                cells = row.find_all("td")
                if len(cells) >= 2:
                    option_name = cells[0].get_text(strip=True)
                    option_price = cells[1].get_text(strip=True)
                    product_info["옵션목록"].append({"옵션명": option_name, "가격": option_price})

        # 상세 이미지 수집
        img_tags = soup.select("#tabPageDetail img")
        detail_imgs = [img['src'] for img in img_tags if img.get('src')]
        product_info["상세이미지 URL"] = detail_imgs

        driver.quit()
        return product_info
    except Exception as e:
        return {"상품명": f"ERROR: {e}", "상품URL": url}

# --------- 이미지 ZIP ---------
def download_images_as_zip(image_urls: List[str], prefix="대표이미지") -> BytesIO:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for i, url in enumerate(image_urls):
            try:
                response = requests.get(url)
                zipf.writestr(f"{prefix}_{i+1}.jpg", response.content)
            except:
                continue
    zip_buffer.seek(0)
    return zip_buffer

# --------- Streamlit UI ---------
st.title("📦 도매꾹 상품 정보 크롤러")

urls_input = st.text_area("도매꾹 상품 URL을 줄바꿈으로 입력하세요:")

if st.button("크롤링 시작"):
    urls = [line.strip() for line in urls_input.strip().splitlines() if line.strip()]
    if not urls:
        st.warning("URL을 하나 이상 입력해주세요.")
    else:
        results = []
        main_images = []
        detail_images = []
        with st.spinner("상품 정보를 수집 중입니다..."):
            for url in urls:
                data = get_product_info_from_url(url)
                # 옵션이 있을 경우 옵션마다 행 생성
                if data.get("옵션목록"):
                    for opt in data["옵션목록"]:
                        row = data.copy()
                        row.update(opt)
                        del row["옵션목록"]
                        results.append(row)
                else:
                    if "옵션목록" in data:
                        del data["옵션목록"]
                    results.append(data)

                if data.get("대표 이미지 URL", "N/A") != "N/A":
                    main_images.append(data["대표 이미지 URL"])
                if data.get("상세이미지 URL"):
                    detail_images.extend(data["상세이미지 URL"])

        df = pd.DataFrame(results)
        st.success("크롤링 완료!")
        st.dataframe(df.drop(columns=["상세이미지 URL", "상품설명 HTML"], errors="ignore"))

        # 엑셀 다운로드
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button("📥 엑셀 다운로드", excel_buffer, file_name="상품정보.xlsx")

        # 이미지 다운로드
        if main_images:
            zip_main = download_images_as_zip(main_images, "대표이미지")
            st.download_button("📸 대표 이미지 ZIP", zip_main, file_name="대표이미지.zip")

        if detail_images:
            zip_detail = download_images_as_zip(detail_images, "상세이미지")
            st.download_button("🖼️ 상세 이미지 ZIP", zip_detail, file_name="상세이미지.zip")

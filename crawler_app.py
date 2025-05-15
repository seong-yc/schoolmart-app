# NOTE: This script requires Streamlit to run.
# To install: pip install streamlit beautifulsoup4

try:
    import streamlit as st
except ModuleNotFoundError:
    raise ModuleNotFoundError("'streamlit' 모듈이 설치되어 있지 않습니다. 아래 명령어로 설치해주세요:\n\npip install streamlit")

import pandas as pd
import os
import requests
import zipfile
from datetime import datetime
from bs4 import BeautifulSoup

st.title("📦 온라인 상품 URL → 학교장터 템플릿 자동 생성기")

st.markdown("""
이 앱은 온라인 상품 URL(도매꾹 포함)을 입력하면:
1. 상품 정보를 자동 수집하고
2. 학교장터 템플릿 형식의 엑셀 파일을 만들고
3. 이미지도 자동 저장하고 ZIP 파일로 다운로드할 수 있습니다 ✅
""")

urls_input = st.text_area("상품 URL 목록 (줄마다 하나씩 입력해주세요)")
submit = st.button("🚀 수집 시작")

if submit:
    urls = [url.strip() for url in urls_input.strip().split('\n') if url.strip() != '']

    collected = []
    image_folder = "images"
    os.makedirs(image_folder, exist_ok=True)

    headers = {"User-Agent": "Mozilla/5.0"}

    for i, url in enumerate(urls):
        # 기본값 설정
        product_name = f"온라인 상품 {i+1}"
        price_text = 50000 + i * 1000
        desc = "이 상품은 고급 자재로 만들어졌으며 학교 납품에 적합합니다."
        image_url = f"https://picsum.photos/seed/{i}/300/200"

        # 도매꾹 상품이면 실제 정보 크롤링 시도
        if "domeggook.com" in url:
            try:
                res = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")

                # 상품명
                title_tag = soup.select_one("meta[property='og:title']") or soup.find("title")
                if title_tag:
                    product_name = title_tag['content'].strip() if title_tag.has_attr('content') else title_tag.text.strip()

                # 이미지 URL
                image_meta = soup.select_one("meta[property='og:image']")
                if image_meta and image_meta.has_attr('content'):
                    image_url = image_meta['content']

                # 가격 (일부 페이지는 노출 안될 수 있음)
                price_tag = soup.select_one(".price-now")
                if price_tag:
                    price_text = price_tag.text.strip()

            except Exception as e:
                st.warning(f"⚠️ 도매꾹 정보 수집 실패: {e}")

        image_name = f"product_{i+1}.jpg"
        image_path = os.path.join(image_folder, image_name)

        try:
            response = requests.get(image_url, timeout=5)
            if response.status_code == 200:
                with open(image_path, "wb") as f:
                    f.write(response.content)
            else:
                st.warning(f"⚠️ 이미지 다운로드 실패 ({response.status_code}) - {image_url}")
        except Exception as e:
            st.warning(f"⚠️ 이미지 저장 오류: {e}")

        collected.append({
            "상품명": product_name,
            "카테고리": "학교비품 > 기타",
            "규격": "1000x500x750mm",
            "단가": price_text,
            "상세설명": desc,
            "이미지파일명": image_name,
            "납품가능지역": "전국",
            "모델명": f"MDL{i+1}",
            "제조사": "공급업체",
            "재고수량": 100,
            "비고": "자동 수집된 상품"
        })

    df = pd.DataFrame(collected)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"학교장터_상품등록_{timestamp}.xlsx"
    df.to_excel(output_filename, index=False)

    # 이미지 ZIP 파일 생성
    zip_filename = f"images_{timestamp}.zip"
    with zipfile.ZipFile(zip_filename, "w") as zipf:
        for file in os.listdir(image_folder):
            file_path = os.path.join(image_folder, file)
            zipf.write(file_path, arcname=file)

    st.success(f"총 {len(df)}개의 상품을 수집했습니다!")

    with open(output_filename, "rb") as f:
        st.download_button("📥 엑셀 다운로드", data=f, file_name=output_filename)

    with open(zip_filename, "rb") as f:
        st.download_button("🖼 이미지 ZIP 다운로드", data=f, file_name=zip_filename)

    st.markdown(f"📁 이미지와 엑셀 파일이 준비되었습니다.")
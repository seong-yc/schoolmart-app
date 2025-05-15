# NOTE: This script requires Streamlit to run.
# To install: pip install streamlit

try:
    import streamlit as st
except ModuleNotFoundError:
    raise ModuleNotFoundError("'streamlit' 모듈이 설치되어 있지 않습니다. 아래 명령어로 설치해주세요:\n\npip install streamlit")

import pandas as pd
import os
import urllib.request
from datetime import datetime

st.title("📦 도매꾹 상품 크롤링 → 학교장터 등록 템플릿 자동 생성기")

st.markdown("""
이 앱은 도매꾹 상품 URL을 입력하면:
1. 상품 정보를 자동 수집하고
2. 학교장터 템플릿 형식의 엑셀 파일을 만들고
3. 이미지도 자동 저장해줍니다 ✅
""")

urls_input = st.text_area("상품 URL 목록 (줄마다 하나씩 입력해주세요)")
submit = st.button("🚀 수집 시작")

if submit:
    urls = [url.strip() for url in urls_input.strip().split('\n') if url.strip() != '']

    # 예시용 수집 결과 리스트
    collected = []
    image_folder = "images"
    os.makedirs(image_folder, exist_ok=True)

    for i, url in enumerate(urls):
        # 실제 크롤링 로직 대신 예시 데이터 삽입 (Selenium 등을 연동해 실제 수집 가능)
        fake_title = f"도매꾹 상품 {i+1}"
        fake_spec = "1000x500x750mm"
        fake_price = 50000 + i * 1000
        fake_desc = "이 상품은 고급 자재로 만들어졌으며 학교 납품에 적합합니다."
        fake_image_url = "https://via.placeholder.com/300x200.png?text=Product+Image"
        fake_image_name = f"product_{i+1}.jpg"

        # 이미지 다운로드
        image_path = os.path.join(image_folder, fake_image_name)
        urllib.request.urlretrieve(fake_image_url, image_path)

        collected.append({
            "상품명": fake_title,
            "카테고리": "학교비품 > 기타",
            "규격": fake_spec,
            "단가": fake_price,
            "상세설명": fake_desc,
            "이미지파일명": fake_image_name,
            "납품가능지역": "전국",
            "모델명": f"MDL{i+1}",
            "제조사": "도매꾹공급업체",
            "재고수량": 100,
            "비고": "자동 수집된 상품"
        })

    # DataFrame 생성 및 엑셀 저장
    df = pd.DataFrame(collected)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"학교장터_상품등록_{timestamp}.xlsx"
    df.to_excel(output_filename, index=False)

    st.success(f"총 {len(df)}개의 상품을 수집했습니다!")
    st.download_button("📥 엑셀 다운로드", data=open(output_filename, "rb"), file_name=output_filename)
    st.markdown(f"🖼 이미지 파일은 `{image_folder}/` 폴더에 저장되었습니다.")

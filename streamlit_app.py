import streamlit as st
import pandas as pd
import zipfile
import requests
from bs4 import BeautifulSoup
from io import BytesIO
from typing import List

# 이미지 압축 다운로드
def download_images_as_zip(image_urls: List[str], prefix="이미지") -> BytesIO:
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zipf:
        for i, url in enumerate(image_urls):
            try:
                response = requests.get(url)
                response.raise_for_status()
                zipf.writestr(f"{prefix}_{i+1}.jpg", response.content)
            except:
                continue
    zip_buffer.seek(0)
    return zip_buffer

# 상품 정보 수집 함수
def get_product_info(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        product_name = soup.select_one("meta[property='og:title']")
        product_name = product_name['content'].strip() if product_name else "제목 없음"

        image_tag = soup.select_one("meta[property='og:image']")
        image_url = image_tag['content'] if image_tag else ""

        price_tag = soup.select_one(".price-now, .product-price, .price")
        price = price_tag.text.strip() if price_tag else ""

        desc_tag = soup.select_one(".product-detail")
        description = desc_tag.get_text(strip=True) if desc_tag else ""

        detail_imgs = soup.select("#tabPageDetail img") or soup.select(".product-detail img")
        detail_image_urls = []
        for img in detail_imgs:
            src = img.get('src')
            if src:
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://www.domeggook.com' + src
                detail_image_urls.append(src)

        return {
            "상품명": product_name,
            "가격": price,
            "대표이미지": image_url,
            "상세설명": description,
            "상세이미지": detail_image_urls,
            "상품URL": url
        }
    except Exception as e:
        return {"상품명": f"❌ 오류: {e}", "상품URL": url}

# Streamlit UI
st.title("🧼 도매꾹 공개 상품 크롤러 (Selenium 없이)")

urls_input = st.text_area("📥 도매꾹 상품 URL 입력 (한 줄에 하나씩)")

if st.button("🚀 상품 정보 수집"):
    urls = [u.strip() for u in urls_input.strip().splitlines() if u.strip()]
    if not urls:
        st.warning("URL을 입력해주세요.")
    else:
        results = []
        all_images = []

        with st.spinner("크롤링 중..."):
            for url in urls:
                data = get_product_info(url)
                all_images.extend([data["대표이미지"]] + data.get("상세이미지", []))
                data["상세이미지"] = ";".join(data.get("상세이미지", []))
                results.append(data)

        df = pd.DataFrame(results)
        st.success(f"{len(df)}개 상품 수집 완료!")
        st.dataframe(df)

        # 엑셀 다운로드
        excel_buffer = BytesIO()
        df.to_excel(excel_buffer, index=False)
        excel_buffer.seek(0)
        st.download_button("📄 엑셀 다운로드", data=excel_buffer, file_name="domeggook_products.xlsx")

        # 이미지 ZIP
        if all_images:
            zip_file = download_images_as_zip(all_images)
            st.download_button("🖼 이미지 ZIP 다운로드", data=zip_file, file_name="images.zip")

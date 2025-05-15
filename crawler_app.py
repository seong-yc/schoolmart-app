import streamlit as st
import pandas as pd
import os
import requests
import zipfile
from datetime import datetime
from bs4 import BeautifulSoup
from PIL import Image
from io import BytesIO

output_dir = "outputs"
image_folder = os.path.join(output_dir, "images")
os.makedirs(image_folder, exist_ok=True)

st.title("🏫 도매꾹 상품 → 학교장터 엑셀 자동 변환기")

st.markdown("""
도매꾹 상품 URL을 입력하면:
- 상품 정보를 정밀하게 수집하고
- 대표 + 상세 이미지 저장
- 학교장터 양식 엑셀 파일과 이미지 ZIP을 생성합니다.
""")

urls_input = st.text_area("🔗 도매꾹 상품 URL 입력 (줄마다 하나)", height=200)
submit = st.button("🚀 상품 정보 수집 및 변환")

if submit:
    urls = [u.strip() for u in urls_input.strip().split('\n') if u.strip()]
    collected = []

    with st.spinner("상품 정보를 수집 중입니다..."):
        for i, url in enumerate(urls):
            try:
                res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
                soup = BeautifulSoup(res.text, "html.parser")

                # 상품명
                title_tag = soup.select_one("meta[property='og:title']")
                if title_tag and title_tag.get('content'):
                    product_name = title_tag['content'].strip()
                else:
                    title_tag = soup.find("title")
                    product_name = title_tag.text.strip() if title_tag else ""

                # 가격
                price_tag = soup.select_one(".price-now")
                if price_tag:
                    price_text = price_tag.text.strip()
                else:
                    price_tag = soup.select_one(".product-price")
                    price_text = price_tag.text.strip() if price_tag else ""

                # 대표 이미지
                image_tag = soup.select_one("meta[property='og:image']")
                if image_tag and image_tag.get('content'):
                    image_url = image_tag['content']
                else:
                    image_tag = soup.select_one(".product-image img")
                    image_url = image_tag['src'] if image_tag and image_tag.get('src') else ""

                # 설명
                desc_tag = soup.select_one(".product-detail")
                desc = desc_tag.get_text(strip=True) if desc_tag else ""

                # 카테고리
                category_tags = soup.select(".location a")
                categories = [tag.get_text(strip=True) for tag in category_tags[1:]]
                category1 = categories[0] if len(categories) > 0 else ""
                category2 = categories[1] if len(categories) > 1 else ""
                category3 = categories[2] if len(categories) > 2 else ""

                # 상세 이미지
                detail_imgs = soup.select("#tabContents img") or soup.select(".product-detail img")
                detail_image_urls = []
                for img in detail_imgs:
                    if img.has_attr('src'):
                        src = img['src']
                        if src.startswith('//'):
                            src = 'https:' + src
                        elif src.startswith('/'):
                            src = 'https://www.domeggook.com' + src
                        detail_image_urls.append(src)

                # 필수 정보 없으면 건너뜀
                if not (product_name and price_text and image_url):
                    st.warning(f"⚠️ 필수 정보 누락 → 제외됨: {url}")
                    continue

                safe_name = product_name.replace(" ", "_").replace("/", "_")
                image_name = f"{safe_name}_main.jpg"
                image_path = os.path.join(image_folder, image_name)

                try:
                    img_data = requests.get(image_url, timeout=5).content
                    with open(image_path, "wb") as f:
                        f.write(img_data)
                except:
                    st.warning(f"⚠️ 대표 이미지 저장 실패: {image_url}")

                detail_image_names = []
                for j, detail_url in enumerate(detail_image_urls):
                    try:
                        response = requests.get(detail_url, timeout=5)
                        if response.status_code == 200:
                            detail_name = f"{safe_name}_detail_{j+1}.jpg"
                            detail_path = os.path.join(image_folder, detail_name)
                            with open(detail_path, "wb") as f:
                                f.write(response.content)
                            detail_image_names.append(detail_name)
                    except:
                        pass

                # 미리보기
                st.subheader(f"📦 {product_name}")
                try:
                    image_preview = Image.open(BytesIO(img_data))
                    st.image(image_preview, caption="대표 이미지", width=200)
                except:
                    st.text("(대표 이미지 미리보기 실패)")

                collected.append({
                    "결과": category1 or "기타",
                    "카테고리1": category1,
                    "카테고리2": category2,
                    "카테고리3": category3,
                    "물품명": product_name,
                    "규격": "",
                    "모델명": "",
                    "제조번호": "",
                    "제조사": "",
                    "제조국": "",
                    "소재/재질": "",
                    "최소주문수량": "",
                    "판매단위": "개",
                    "보증기간": "",
                    "납품 가능기한": "",
                    "배송비종류": "",
                    "배송비": "",
                    "타품 배송비": "",
                    "배송유예": "",
                    "제주배송여부": "",
                    "제주추가배송비": "",
                    "제주추가배송여부": "",
                    "상품상세설명": desc,
                    "대표이미지1": image_name,
                    "상세이미지": ";".join(detail_image_names)
                })

            except Exception as e:
                st.error(f"❌ 수집 실패: {url} → {e}")

    if collected:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        excel_path = os.path.join(output_dir, f"학교장터_상품등록_{timestamp}.xlsx")
        zip_path = os.path.join(output_dir, f"images_{timestamp}.zip")

        df = pd.DataFrame(collected)
        df.to_excel(excel_path, index=False)

        with zipfile.ZipFile(zip_path, "w") as zipf:
            for file in os.listdir(image_folder):
                zipf.write(os.path.join(image_folder, file), arcname=file)

        st.success(f"✅ 총 {len(df)}개 상품 정리 완료!")
        with open(excel_path, "rb") as f:
            st.download_button("📥 엑셀 다운로드", data=f, file_name=os.path.basename(excel_path))
        with open(zip_path, "rb") as f:
            st.download_button("🖼 이미지 ZIP 다운로드", data=f, file_name=os.path.basename(zip_path))
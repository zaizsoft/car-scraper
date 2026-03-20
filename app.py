import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time

# إعدادات الصفحة
st.set_page_config(page_title="Ouedkniss Scraper", layout="wide")
st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🚗 سحب بيانات السيارات</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>أدخل رابط صفحة السيارات</p>", unsafe_allow_html=True)

default_url = "https://www.ouedkniss.com/automobiles_vehicules/1"
url_input = st.text_input("رابط الصفحة:", default_url)

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.binary_location = "/usr/bin/chromium"
    service = Service(executable_path="/usr/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def scrape_cars(url):
    driver = get_driver()
    car_data = []
    
    try:
        with st.spinner("جاري تحميل الصفحة..."):
            driver.get(url)
            
            # ننتظر ظهور أي محتوى في الصفحة
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # التمرير لأسفل عدة مرات لتحميل السيارات (لأن الموقع يستخدم التحميل الكسول)
            last_height = driver.execute_script("return document.body.scrollHeight")
            for _ in range(3): # نكرر التمرير 3 مرات
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight - 500);")
                time.sleep(1)

            soup = BeautifulSoup(driver.page_source, 'lxml')
            
            # استراتيجية جديدة: البحث عن أي رابط يحتوي على كلمة "annonce" أو "automobile"
            # هذا يجمع روابط السيارات بغض النظر عن شكل التصميم
            links = soup.find_all('a', href=True)
            car_links = [a for a in links if '/automobiles_vehicules' in a['href'] and '/1' not in a['href']]

            # استخراج البيانات من هذه الروابط
            processed_hrefs = set() # لتجنب تكرار نفس السيارة
            
            for link in car_links:
                href = link['href']
                if href in processed_hrefs:
                    continue
                processed_hrefs.add(href)

                # البحث عن العنوان داخل الرابط
                title = "سيارة"
                # ممكن يكون العنوان في خاصية alt للصورة أو في نص الرابط
                img_tag = link.find('img')
                if img_tag and img_tag.get('alt'):
                    title = img_tag.get('alt')
                elif link.text.strip():
                    title = link.text.strip()

                # البحث عن الصورة
                img_url = None
                if img_tag:
                    img_url = img_tag.get('data-src') or img_tag.get('src')
                    if img_url and not img_url.startswith('http'):
                        img_url = "https://www.ouedkniss.com" + img_url
                
                # البحث عن السعر (غالبا يكون في span بجانب الرابط أو بداخله)
                price = "سعر غير محدد"
                # نبحث في العناصر القريبة
                parent = link.find_parent('div', class_=lambda x: x and 'classified' in str(x).lower())
                if not parent:
                    parent = link.find_parent('div', recursive=True) # نبحث في الأب المباشر
                
                if parent:
                    price_span = parent.find('span', class_=lambda x: x and 'price' in str(x).lower())
                    if not price_span:
                        # بحث أوسع عن أي نص يشبه السعر
                        texts = parent.find_all(string=True)
                        for t in texts:
                            if 'د.ج' in t or 'DA' in t:
                                price = t.strip()
                                break
                
                if img_url:
                    car_data.append({
                        'title': title,
                        'price': price,
                        'image': img_url
                    })

    except Exception as e:
        import traceback
        st.error(f"حدث خطأ: {e}")
        st.text(traceback.format_exc())
    finally:
        driver.quit()
        
    return car_data

if st.button("استخراج البيانات"):
    if url_input:
        cars = scrape_cars(url_input)
        if cars:
            st.success(f"تم العثور على {len(cars)} سيارة!")
            cols = st.columns(3)
            for idx, car in enumerate(cars):
                with cols[idx % 3]:
                    st.markdown(f"""
                    <div style='border: 1px solid #ddd; border-radius: 10px; padding: 10px; margin-bottom: 10px; text-align: center; background-color: #f9f9f9;'>
                        <h3 style='font-size: 16px; color: #333; height: 40px; overflow: hidden;'>{car['title']}</h3>
                        <img src='{car['image']}' width='100%' style='border-radius: 5px; height: 150px; object-fit: cover;'>
                        <p style='color: #e74c3c; font-weight: bold; font-size: 18px; margin-top: 5px;'>{car['price']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("لم يتم العثور على نتائج. قد يكون الموقع بطيئاً أو تم حجب الوصول مؤقتاً.")
    else:
        st.warning("الرجاء إدخال الرابط.")

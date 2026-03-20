import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import shutil

# إعدادات الصفحة
st.set_page_config(page_title="Ouedkniss Scraper", layout="wide")

# عنوان التطبيق
st.markdown("<h1 style='text-align: center; color: #ff4b4b;'>🚗 سحب بيانات السيارات من Ouedkniss</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center;'>أدخل رابط صفحة السيارات للحصول على البيانات</p>", unsafe_allow_html=True)

default_url = "https://www.ouedkniss.com/automobiles_vehicules/1"
url_input = st.text_input("رابط الصفحة:", default_url)

def get_driver():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36")
    
    # إعداد السيرفر (Linux/Chromium) للعمل على Streamlit Cloud
    if shutil.which("chromium-browser"):
        options.binary_location = shutil.which("chromium-browser")
    
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    except:
        # خيار بديل إذا فشل التحميل التلقائي
        driver = webdriver.Chrome(options=options)
        
    return driver

def scrape_cars(url):
    driver = get_driver()
    car_data = []
    
    try:
        with st.spinner("جاري تحميل البيانات... يرجى الانتظار"):
            driver.get(url)
            
            # انتظار تحميل الأسعار
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "price"))
            )
            
            # التمرير لتحميل الصور
            driver.execute_script("window.scrollTo(0, 2000);")
            time.sleep(2)

            soup = BeautifulSoup(driver.page_source, 'html.parser')
            
            # البحث عن عناصر السيارات (قد تتغير الأسماء)
            listings = soup.find_all('div', class_='classified')
            if not listings:
                listings = soup.find_all('div', class_='annonce')

            for car in listings:
                try:
                    title_tag = car.find('h2') or car.find('h3')
                    title = title_tag.get_text(strip=True) if title_tag else "غير معروف"

                    price_tag = car.find('div', class_='price')
                    price = price_tag.get_text(strip=True) if price_tag else "السعر غير متوفر"

                    img_tag = car.find('img')
                    img_url = img_tag.get('data-src') or img_tag.get('src') if img_tag else None
                    
                    if img_url and not img_url.startswith('http'):
                        img_url = "https://www.ouedkniss.com" + img_url

                    if title != "غير معروف":
                        car_data.append({
                            'title': title,
                            'price': price,
                            'image': img_url
                        })
                except Exception:
                    continue

    except Exception as e:
        st.error(f"حدث خطأ: {e}")
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
                        <h3 style='font-size: 16px; color: #333;'>{car['title']}</h3>
                        <img src='{car['image']}' width='100%' style='border-radius: 5px;'>
                        <p style='color: #e74c3c; font-weight: bold; font-size: 18px;'>{car['price']}</p>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            st.warning("لم يتم العثور على نتائج.")

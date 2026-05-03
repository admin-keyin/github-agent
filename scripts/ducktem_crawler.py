import os
import sys
import requests
import json
import time
import re
import argparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv

# .env.local 로드 (로컬 실행 시)
if os.path.exists('.env.local'):
    load_dotenv(dotenv_path='.env.local')

# 환경 변수 우선순위: 1. 시스템 환경변수(GitHub Actions) 2. .env.local
SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL') or os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

def validate_config():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 에러: SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.")
        print("GitHub Secrets 또는 .env.local 파일을 확인해주세요.")
        sys.exit(1)

    if not SUPABASE_URL.startswith('http'):
        print(f"❌ 에러: 잘못된 SUPABASE_URL 형식입니다: {SUPABASE_URL}")
        sys.exit(1)

# 설정 검증 실행
validate_config()

HEADERS_SUPA = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

class DucktemCrawler:
    def __init__(self, keyword, animation_id):
        self.keyword = keyword
        self.animation_id = animation_id
        self.results = []

    def save(self):
        if not self.results:
            print(f"⚠️ '{self.keyword}' 수집된 결과가 없습니다.")
            return
        
        data = []
        for i in self.results:
            item = {
                "title": i['title'][:200],
                "price": int(i['price'] or 0),
                "image_url": i['image'],
                "source_url": i['url'],
                "source_platform": i['platform'],
                "animation_id": self.animation_id
            }
            # country_code는 DB에 컬럼이 있을 때만 추가되도록 (현재는 제외하여 에러 방지)
            data.append(item)
        
        try:
            res = requests.post(f"{SUPABASE_URL}/rest/v1/goods", headers=HEADERS_SUPA, data=json.dumps(data))
            if res.status_code in [200, 201]:
                print(f"✅ '{self.keyword}' ({len(data)}개) DB 동기화 완료")
            elif res.status_code == 409:
                print(f"ℹ️ '{self.keyword}' 중복된 데이터는 건너뛰었습니다.")
            else:
                print(f"❌ '{self.keyword}' 저장 실패: {res.status_code} {res.text[:100]}")
        except Exception as e:
            print(f"❌ DB 통신 에러: {e}")

    def crawl_bunjang(self):
        try:
            url = f"https://api.bunjang.co.kr/api/1/find_v2.json?q={self.keyword}&order=date&n=20"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            if res.status_code == 200:
                for i in res.json().get('list', []):
                    self.results.append({
                        "title": i.get('name'), "price": i.get('price'), "image": i.get('product_image'),
                        "url": f"https://m.bunjang.co.kr/products/{i.get('pid')}", "platform": "Bunjang", "country": "KR"
                    })
        except: pass

    def crawl_daangn(self):
        try:
            url = f"https://www.daangn.com/search/{self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.article-tile')[:15]:
                title_el = el.select_one('.article-title')
                price_el = el.select_one('.article-price')
                img_el = el.select_one('.card-photo img')
                link_el = el.select_one('a')
                if title_el and price_el:
                    price = int(re.sub(r'[^\d]', '', price_el.text)) if '나눔' not in price_el.text else 0
                    self.results.append({
                        "title": f"[당근] {title_el.text.strip()}", "price": price, 
                        "image": img_el.get('src') if img_el else "", 
                        "url": "https://www.daangn.com" + link_el.get('href'), 
                        "platform": "Daangn", "country": "KR"
                    })
        except: pass

    def crawl_ittanstore(self):
        try:
            url = f"https://ittanstore.com/product/search.html?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.prdList > li'):
                name_el = el.select_one('.name a')
                price_el = el.select_one('.xans-record- span')
                img_el = el.select_one('.thumbnail img')
                if name_el and img_el:
                    price_text = price_el.text.strip() if price_el else "0"
                    price = int(re.sub(r'[^\d]', '', price_text)) if price_text else 0
                    img_src = img_el.get('src')
                    if img_src.startswith('//'): img_src = "https:" + img_src
                    self.results.append({
                        "title": f"[이딴가게] {name_el.text.strip()}", "price": price, 
                        "image": img_src, "url": "https://ittanstore.com" + name_el.get('href'), 
                        "platform": "IttanStore", "country": "KR"
                    })
        except: pass

    def crawl_dokidokigoods(self):
        try:
            url = f"https://dokidokigoods.co.kr/product/search.html?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.prdList > li'):
                name_el = el.select_one('.description .name a')
                price_el = el.select_one('.description .price') 
                img_el = el.select_one('.thumbnail img')
                if name_el and img_el:
                    price_text = price_el.text.strip() if price_el else "0"
                    price = int(re.sub(r'[^\d]', '', price_text)) if price_text else 0
                    img_src = img_el.get('src')
                    if img_src.startswith('//'): img_src = "https:" + img_src
                    self.results.append({
                        "title": f"[두근두근] {name_el.text.strip()}", "price": price, 
                        "image": img_src, "url": "https://dokidokigoods.co.kr" + name_el.get('href'), 
                        "platform": "DokiDoki", "country": "KR"
                    })
        except: pass

    def crawl_heyprice(self):
        try:
            url = f"https://heyprice.co.kr/search/yahoo_auction?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.item-box')[:10]:
                title = el.select_one('.item-name').text.strip()
                price = int(re.sub(r'[^\d]', '', el.select_one('.item-price').text))
                img = el.select_one('img').get('src')
                self.results.append({"title": f"[해외직구] {title}", "price": price, "image": img, "url": "https://heyprice.co.kr" + el.select_one('a').get('href'), "platform": "HeyPrice", "country": "JP"})
        except: pass

    def crawl_bidbuy(self):
        try:
            url = f"https://www.bidbuy.co.kr/auctions/japan/search?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.item_list_box')[:10]:
                title_el = el.select_one('.item_name')
                price_el = el.select_one('.price_won')
                img_el = el.select_one('.item_img img')
                if title_el and price_el:
                    price = int(re.sub(r'[^\d]', '', price_el.text))
                    self.results.append({"title": f"[비드바이] {title_el.text.strip()}", "price": price, "image": img_el.get('src') if img_el else "", "url": "https://www.bidbuy.co.kr" + el.select_one('a').get('href'), "platform": "Bidbuy", "country": "JP"})
        except: pass

    def crawl_yahoo_jp(self):
        try:
            url = f"https://auctions.yahoo.co.jp/search/search?p={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.Product')[:10]:
                title_el = el.select_one('.Product__titleLink')
                price_el = el.select_one('.Product__priceValue')
                if title_el and price_el:
                    price = int(re.sub(r'[^\d]', '', price_el.text)) * 9
                    self.results.append({"title": title_el.text.strip(), "price": price, "image": el.select_one('.Product__imageData').get('src', ''), "url": title_el.get('href'), "platform": "Yahoo Auctions", "country": "JP"})
        except: pass

    def crawl_ebay_us(self):
        try:
            url = f"https://www.ebay.com/sch/i.html?_nkw={self.keyword.replace(' ', '+')}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.s-item__wrapper')[:10]:
                title = el.select_one('.s-item__title')
                price_el = el.select_one('.s-item__price')
                if title and price_el:
                    p_str = re.sub(r'[^\d.]', '', price_el.text.split('to')[0])
                    price = int(float(p_str) * 1400) if p_str else 0
                    self.results.append({"title": title.text.strip(), "price": price, "image": el.select_one('.s-item__image-img img').get('src', ''), "url": el.select_one('.s-item__link').get('href'), "platform": "eBay", "country": "US"})
        except: pass

class DucktemEventCrawler:
    def __init__(self):
        self.events = []

    def crawl_animate_korea(self):
        print("🎨 [Animate KR] 공식 이벤트 수집 중...")
        try:
            url = "https://www.animate-onlineshop.co.kr/goods/event.php"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.event_list li')[:5]:
                title_el = el.select_one('.event_title')
                if title_el:
                    self.events.append({
                        "title": f"[Animate KR] {title_el.text.strip()}",
                        "start_date": datetime.now().strftime('%Y-%m-%d'),
                        "end_date": (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                        "location": "애니메이트 매장",
                        "detail_link": "https://www.animate-onlineshop.co.kr" + el.select_one('a').get('href')
                    })
        except: pass

    def save(self):
        if not self.events: return
        requests.post(f"{SUPABASE_URL}/rest/v1/events", headers=HEADERS_SUPA, data=json.dumps(self.events))

def get_or_create_animation(title):
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/animations?title=eq.{title}", headers=HEADERS_SUPA)
        data = res.json()
        if data: return data[0]['id']
        res = requests.post(f"{SUPABASE_URL}/rest/v1/animations", headers=HEADERS_SUPA, data=json.dumps({"title": title}))
        res = requests.get(f"{SUPABASE_URL}/rest/v1/animations?title=eq.{title}", headers=HEADERS_SUPA)
        return res.json()[0]['id'] if res.json() else None
    except: return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', type=str)
    args = parser.parse_args()

    genres = [
        {"title": "나루토", "kws": ["나루토", "Naruto", "ナルト"]},
        {"title": "짱구는못말려", "kws": ["짱구", "Crayon Shin-chan"]},
        {"title": "치이카와", "kws": ["치이카와", "Chiikawa"]},
        {"title": "하이큐", "kws": ["하이큐", "Haikyuu"]},
        {"title": "주술회전", "kws": ["주술회전", "Jujutsu Kaisen"]},
        {"title": "귀멸의 칼날", "kws": ["귀멸", "Demon Slayer"]},
        {"title": "슬램덩크", "kws": ["슬램덩크", "Slam Dunk"]},
        {"title": "명탐정코난", "kws": ["명탐정 코난", "Detective Conan"]}
    ]

    if args.keyword:
        print(f"🚀 집중 수집 시작: {args.keyword}")
        anim_id = get_or_create_animation("기타/요청")
        c = DucktemCrawler(args.keyword, anim_id)
        c.crawl_bunjang(); c.crawl_daangn(); c.crawl_ittanstore(); c.crawl_dokidokigoods()
        c.crawl_heyprice(); c.crawl_bidbuy(); c.crawl_yahoo_jp(); c.crawl_ebay_us(); c.save()
        return

    for g in genres:
        anim_id = get_or_create_animation(g['title'])
        for kw in g['kws']:
            c = DucktemCrawler(kw, anim_id)
            c.crawl_bunjang(); c.crawl_daangn(); c.crawl_ittanstore(); c.crawl_dokidokigoods()
            c.crawl_heyprice(); c.crawl_bidbuy(); c.crawl_yahoo_jp(); c.crawl_ebay_us(); c.save()
            time.sleep(1)
        print(f"✅ {g['title']} 동기화 완료")

    e = DucktemEventCrawler()
    e.crawl_animate_korea()
    e.save()
    print("📅 공식 이벤트 동기화 완료")

if __name__ == "__main__":
    main()

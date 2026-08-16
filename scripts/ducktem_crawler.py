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

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL') or os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY') or os.getenv('SUPABASE_KEY') or os.getenv('SUPABASE_ANON_KEY')

def validate_config():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ 에러: SUPABASE_URL 또는 SUPABASE_KEY가 설정되지 않았습니다.")
        sys.exit(1)

validate_config()

HEADERS_SUPA = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

BROWSER_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7,ja;q=0.6,zh-CN;q=0.5"
}

class DucktemCrawler:
    def __init__(self, keywords, animation_id):
        self.keywords = keywords # {'ko': '...', 'ja': '...', 'en': '...', 'zh': '...'}
        self.animation_id = animation_id
        self.results = []

    def save(self):
        if not self.results:
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
            data.append(item)
        
        try:
            res = requests.post(f"{SUPABASE_URL}/rest/v1/goods", headers=HEADERS_SUPA, data=json.dumps(data))
            if res.status_code in [200, 201]:
                print(f"✅ DB 동기화 완료 ({len(data)}개)")
            elif res.status_code == 409:
                pass 
            else:
                print(f"❌ 저장 실패: {res.status_code} {res.text[:100]}")
        except Exception as e:
            print(f"❌ DB 통신 에러: {e}")

    def crawl_bunjang(self):
        kw = self.keywords.get('ko')
        try:
            url = f"https://api.bunjang.co.kr/api/1/find_v2.json?q={kw}&order=date&n=20"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            if res.status_code == 200:
                for i in res.json().get('list', []):
                    if i.get('status') not in ['0', 0]: continue
                    price = int(i.get('price') or 0)
                    if price <= 0: continue
                    self.results.append({
                        "title": i.get('name'), "price": price, "image": i.get('product_image'),
                        "url": f"https://m.bunjang.co.kr/products/{i.get('pid')}", "platform": "Bunjang"
                    })
        except: pass

    def crawl_daangn(self):
        kw = self.keywords.get('ko')
        try:
            url = f"https://www.daangn.com/search/{kw}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.article-tile')[:10]:
                title_el = el.select_one('.article-title')
                price_el = el.select_one('.article-price')
                if title_el and price_el:
                    price_text = price_el.text.strip()
                    price = int(re.sub(r'[^\d]', '', price_text)) if re.sub(r'[^\d]', '', price_text) else 0
                    if price <= 0 and '나눔' not in price_text: continue
                    self.results.append({
                        "title": f"[당근] {title_el.text.strip()}", "price": price, 
                        "image": el.select_one('.card-photo img').get('src', ''), 
                        "url": "https://www.daangn.com" + el.select_one('a').get('href'), 
                        "platform": "Daangn"
                    })
        except: pass

    def crawl_yahoo_jp(self):
        kw = self.keywords.get('ja')
        try:
            url = f"https://auctions.yahoo.co.jp/search/search?p={kw}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.Product')[:10]:
                title_el = el.select_one('.Product__titleLink')
                price_el = el.select_one('.Product__priceValue')
                if title_el and price_el:
                    # 입찰 중이거나 즉시구매가 있는 것만 (엔화 -> 원화 약 9배 계산)
                    price = int(re.sub(r'[^\d]', '', price_el.text)) * 9
                    self.results.append({
                        "title": f"[야후재팬] {title_el.text.strip()}", "price": price, 
                        "image": el.select_one('.Product__imageData').get('src', ''), 
                        "url": title_el.get('href'), "platform": "Yahoo Auctions"
                    })
        except: pass

    def crawl_ebay(self):
        kw = self.keywords.get('en')
        try:
            url = f"https://www.ebay.com/sch/i.html?_nkw={kw.replace(' ', '+')}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.s-item__wrapper')[:10]:
                title = el.select_one('.s-item__title')
                price_el = el.select_one('.s-item__price')
                if title and price_el:
                    p_str = re.sub(r'[^\d.]', '', price_el.text.split('to')[0])
                    price = int(float(p_str) * 1400) if p_str else 0
                    if price <= 0: continue
                    self.results.append({
                        "title": f"[eBay] {title.text.strip()}", "price": price, 
                        "image": el.select_one('.s-item__image-img img').get('src', ''), 
                        "url": el.select_one('.s-item__link').get('href'), "platform": "eBay"
                    })
        except: pass

    def crawl_xianyu(self):
        """중국 시엔위(Goofish) 크롤링 - 현재 웹 검색은 제한적이므로 모바일 웹 엔드포인트나 우회 경로 시도"""
        kw = self.keywords.get('zh')
        print(f"🇨🇳 [시엔위] '{kw}' 검색 중...")
        try:
            # 시엔위는 일반 웹 검색이 막혀있는 경우가 많아 검색 결과 페이지의 구조가 바뀔 수 있음
            # 일단 m.ele.me 또는 타오바오 연동 경로를 통한 접근 시도 (가상)
            url = f"https://s.2.taobao.com/list/list.htm?q={kw}" 
            # 실제로는 시엔위 앱 API나 특정 쿠키가 필요함. 여기선 구조적 추가만 진행.
            # 사용자가 계정을 제공하면 이 부분에 쿠키 세션을 적용할 예정.
            pass
        except: pass

    def crawl_all(self):
        self.crawl_bunjang()
        self.crawl_daangn()
        self.crawl_yahoo_jp()
        self.crawl_ebay()
        self.crawl_xianyu()

def get_or_create_animation(title):
    try:
        res = requests.get(f"{SUPABASE_URL}/rest/v1/animations?title=eq.{title}", headers=HEADERS_SUPA)
        data = res.json()
        if data: return data[0]['id']
        requests.post(f"{SUPABASE_URL}/rest/v1/animations", headers=HEADERS_SUPA, data=json.dumps({"title": title}))
        res = requests.get(f"{SUPABASE_URL}/rest/v1/animations?title=eq.{title}", headers=HEADERS_SUPA)
        return res.json()[0]['id'] if res.json() else None
    except: return None

def main():
    # 국가별 언어 매핑 데이터
    genres = [
        {
            "title": "나루토", 
            "keywords": {"ko": "나루토", "en": "Naruto", "ja": "ナルト", "zh": "火影忍者"}
        },
        {
            "title": "짱구는못말려", 
            "keywords": {"ko": "짱구", "en": "Crayon Shin-chan", "ja": "クレヨンしんちゃん", "zh": "蜡笔小新"}
        },
        {
            "title": "치이카와", 
            "keywords": {"ko": "치이카와", "en": "Chiikawa", "ja": "ちいかわ", "zh": "吉伊卡哇"}
        },
        {
            "title": "하이큐", 
            "keywords": {"ko": "하이큐", "en": "Haikyuu", "ja": "ハイキュー", "zh": "排球少年"}
        },
        {
            "title": "주술회전", 
            "keywords": {"ko": "주술회전", "en": "Jujutsu Kaisen", "ja": "呪術廻戦", "zh": "咒术回战"}
        },
        {
            "title": "귀멸의 칼날", 
            "keywords": {"ko": "귀멸", "en": "Demon Slayer", "ja": "鬼滅の刃", "zh": "鬼灭之刃"}
        },
        {
            "title": "슬램덩크", 
            "keywords": {"ko": "슬램덩크", "en": "Slam Dunk", "ja": "スラムダンク", "zh": "灌篮高手"}
        },
        {
            "title": "명탐정코난", 
            "keywords": {"ko": "명탐정 코난", "en": "Detective Conan", "ja": "名探偵コナン", "zh": "名侦探柯南"}
        }
    ]

    for g in genres:
        print(f"🚀 {g['title']} 수집 시작...")
        anim_id = get_or_create_animation(g['title'])
        if not anim_id: continue
        
        crawler = DucktemCrawler(g['keywords'], anim_id)
        crawler.crawl_all()
        crawler.save()
        time.sleep(2)

if __name__ == "__main__":
    main()

import os
import requests
import json
import time
import re
import argparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv(dotenv_path='.env.local')

SUPABASE_URL = os.getenv('NEXT_PUBLIC_SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

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
        if not self.results: return
        data = []
        for i in self.results:
            data.append({
                "title": i['title'][:200],
                "price": int(i['price'] or 0),
                "image_url": i['image'],
                "source_url": i['url'],
                "source_platform": i['platform'],
                "country_code": i['country'],
                "animation_id": self.animation_id
            })
        requests.post(f"{SUPABASE_URL}/rest/v1/goods", headers=HEADERS_SUPA, data=json.dumps(data))

    def crawl_bunjang(self):
        try:
            url = f"https://api.bunjang.co.kr/api/1/find_v2.json?q={self.keyword}&order=date&n=20"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            for i in res.json().get('list', []):
                self.results.append({
                    "title": i.get('name'), "price": i.get('price'), "image": i.get('product_image'),
                    "url": f"https://m.bunjang.co.kr/products/{i.get('pid')}", "platform": "Bunjang", "country": "KR"
                })
        except: pass

    def crawl_dokidokigoods(self):
        """국내 굿즈샵: 두근두근굿즈 수집"""
        print(f"💓 [DokiDoki] '{self.keyword}' 수집 중...")
        try:
            url = f"https://dokidokigoods.co.kr/product/search.html?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            
            # 두근두근굿즈 상품 리스트 파싱
            for el in soup.select('.prdList > li'):
                name_el = el.select_one('.description .name a')
                price_el = el.select_one('.description .price') 
                img_el = el.select_one('.thumbnail img')
                
                if name_el and img_el:
                    title = name_el.text.strip()
                    price_text = price_el.text.strip() if price_el else "0"
                    price = int(re.sub(r'[^\d]', '', price_text)) if price_text else 0
                    link = "https://dokidokigoods.co.kr" + name_el.get('href')
                    
                    self.results.append({
                        "title": f"[두근두근] {title}", "price": price, 
                        "image": "https:" + img_el.get('src') if img_el.get('src').startswith('//') else img_el.get('src'), 
                        "url": link, "platform": "DokiDoki", "country": "KR"
                    })
        except Exception as e:
            print(f"DokiDoki Error: {e}")

    def crawl_ittanstore(self):
        """국내 정품 굿즈샵: 이딴가게 수집"""
        print(f"📦 [IttanStore] '{self.keyword}' 수집 중...")
        # 이딴가게 검색 또는 카테고리 기반 수집
        try:
            # 검색어 기반 수집
            url = f"https://ittanstore.com/product/search.html?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            
            # 이딴가게 상품 리스트 파싱 (Cafe24 기반 구조)
            for el in soup.select('.prdList > li'):
                name_el = el.select_one('.name a')
                price_el = el.select_one('.xans-record- span') # 가격 요소
                img_el = el.select_one('.thumbnail img')
                
                if name_el and img_el:
                    title = name_el.text.strip()
                    price_text = price_el.text.strip() if price_el else "0"
                    price = int(re.sub(r'[^\d]', '', price_text)) if price_text else 0
                    link = "https://ittanstore.com" + name_el.get('href')
                    
                    self.results.append({
                        "title": f"[이딴가게] {title}", "price": price, 
                        "image": "https:" + img_el.get('src') if img_el.get('src').startswith('//') else img_el.get('src'), 
                        "url": link, "platform": "IttanStore", "country": "KR"
                    })
        except Exception as e:
            print(f"IttanStore Error: {e}")

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

    def crawl_heyprice(self):
        try:
            url = f"https://heyprice.co.kr/search/yahoo_auction?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.item-box')[:10]:
                title = el.select_one('.item-name').text.strip()
                price = int(re.sub(r'[^\d]', '', el.select_one('.item-price').text))
                img = el.select_one('img').get('src')
                link = "https://heyprice.co.kr" + el.select_one('a').get('href')
                self.results.append({"title": f"[해외직구] {title}", "price": price, "image": img, "url": link, "platform": "HeyPrice", "country": "JP"})
        except: pass

    def crawl_bidbuy(self):
        try:
            url = f"https://www.bidbuy.co.kr/auctions/japan/search?keyword={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.item_list_box')[:10]:
                title = el.select_one('.item_name').text.strip()
                price = int(re.sub(r'[^\d]', '', el.select_one('.price_won').text))
                img = el.select_one('.item_img img').get('src')
                link = "https://www.bidbuy.co.kr" + el.select_one('a').get('href')
                self.results.append({"title": f"[비드바이] {title}", "price": price, "image": img, "url": link, "platform": "Bidbuy", "country": "JP"})
        except: pass

    def crawl_yahoo_jp(self):
        try:
            url = f"https://auctions.yahoo.co.jp/search/search?p={self.keyword}"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            for el in soup.select('.Product')[:15]:
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
            for el in soup.select('.s-item__wrapper')[:15]:
                title = el.select_one('.s-item__title')
                price_el = el.select_one('.s-item__price')
                if title and price_el:
                    p_str = re.sub(r'[^\d.]', '', price_el.text.split('to')[0])
                    price = int(float(p_str) * 1400) if p_str else 0
                    self.results.append({"title": title.text.strip(), "price": price, "image": el.select_one('.s-item__image-img img').get('src', ''), "url": el.select_one('.s-item__link').get('href'), "platform": "eBay", "country": "US"})
        except: pass

class DucktemEventCrawler:
    """공식 팝업스토어 및 이벤트 크롤러"""
    def __init__(self):
        self.events = []

    def crawl_hyundai_popups(self):
        """더현대/현대백화점 공식 팝업 정보 파싱"""
        print("🏢 [Hyundai] 공식 팝업 정보 수집 중...")
        # 실제 운영 시 현대백화점 이벤트 페이지(https://www.ehyundai.com/newGP/EV/EV000001_L.do) 파싱
        # 현재는 구조적 수집 틀 마련
        pass

    def crawl_animate_korea(self):
        """애니메이트 코리아 공식 이벤트 수집"""
        print("🎨 [Animate KR] 공식 이벤트 수집 중...")
        try:
            url = "https://www.animate-onlineshop.co.kr/goods/event.php"
            res = requests.get(url, headers=BROWSER_HEADERS, timeout=10)
            soup = BeautifulSoup(res.text, 'lxml')
            # 애니메이트 이벤트 페이지 구조에 맞춰 파싱 (예시 셀렉터)
            for el in soup.select('.event_list li')[:5]:
                title = el.select_one('.event_title').text.strip()
                link = "https://www.animate-onlineshop.co.kr" + el.select_one('a').get('href')
                # 실제 날짜 파싱 로직 추가 가능
                self.events.append({
                    "title": f"[Animate KR] {title}",
                    "start_date": datetime.now().strftime('%Y-%m-%d'),
                    "end_date": (datetime.now() + timedelta(days=14)).strftime('%Y-%m-%d'),
                    "location": "애니메이트 매장 (홍대/부산 등)",
                    "detail_link": link
                })
        except: pass

    def save(self):
        if not self.events: return
        # 중복 방지를 위해 title을 기준으로 체크하거나 Upsert 활용
        requests.post(f"{SUPABASE_URL}/rest/v1/events", headers=HEADERS_SUPA, data=json.dumps(self.events))

def get_or_create_animation(title):
    res = requests.get(f"{SUPABASE_URL}/rest/v1/animations?title=eq.{title}", headers=HEADERS_SUPA)
    data = res.json()
    if data: return data[0]['id']
    res = requests.post(f"{SUPABASE_URL}/rest/v1/animations", headers=HEADERS_SUPA, data=json.dumps({"title": title}))
    res = requests.get(f"{SUPABASE_URL}/rest/v1/animations?title=eq.{title}", headers=HEADERS_SUPA)
    return res.json()[0]['id'] if res.json() else None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--keyword', type=str)
    args = parser.parse_args()

    genres = [
        {"title": "나루토", "kws": [
            "나루토 원단", "Naruto fabric", "ナルト 生地",
            "나루토 피규어", "Naruto figure", "ナルト フィギュア",
            "나루토 인형", "Naruto plush", "ナルト ぬいぐるみ",
            "나루토 굿즈", "Naruto goods", "ナルト グッズ",
            "나루토 한정판", "Naruto limited", "ナルト 限定"
        ]},
        {"title": "짱구는못말려", "kws": ["짱구", "Crayon Shin-chan", "クレヨンしんちゃん"]},
        {"title": "도라에몽", "kws": ["도라에몽", "Doraemon", "ドラえもん"]},
        {"title": "산리오", "kws": ["산리오", "Sanrio", "サンリオ"]},
        {"title": "치이카와", "kws": ["치이카와", "Chiikawa", "ちいかわ"]},
        {"title": "카드캡터체리", "kws": ["카드캡터체리", "Cardcaptor Sakura", "カードキャプターさくら"]},
        {"title": "세일러문", "kws": ["세일러문", "Sailor Moon", "セーラームーン"]},
        {"title": "슈가슈가룬", "kws": ["슈가슈가룬", "Sugar Sugar Rune", "シュガシュガルーン"]},
        {"title": "케로로", "kws": ["케로로", "Keroro", "ケロロ軍曹"]},
        {"title": "원피스", "kws": ["원피스 굿즈", "One Piece", "ワンピース"]},
        {"title": "블리치", "kws": ["블리치", "Bleach", "ブリーチ"]},
        {"title": "나의히어로아카데미아", "kws": ["히로아카", "My Hero Academia", "僕のヒーローアカデミア"]},
        {"title": "톰과제리", "kws": ["톰과제리", "Tom and Jerry", "トムとジェリー"]},
        {"title": "괴수8호", "kws": ["괴수8호", "Kaiju No. 8", "怪獣8号"]},
        {"title": "문호스트레이독스", "kws": ["문스독", "Bungo Stray Dogs", "文豪ストレイドッグ스"]},
        {"title": "데스노트", "kws": ["데스노트", "Death Note", "デスノート"]},
        {"title": "주술회전", "kws": ["주술회전", "Jujutsu Kaisen", "呪術廻戦"]},
        {"title": "귀멸의 칼날", "kws": ["귀멸", "Demon Slayer", "鬼滅の刃"]},
        {"title": "슬램덩크", "kws": ["슬램덩크", "Slam Dunk", "スラムダン크"]},
        {"title": "헌터x헌터", "kws": ["헌터x헌터", "Hunter x Hunter", "ハンターハンター"]},
        {"title": "사카모토데이즈", "kws": ["사카모토 데이즈", "Sakamoto Days", "サカモトデイズ"]},
        {"title": "윈드브레이커", "kws": ["윈드브레이커", "Wind Breaker", "ウィンドブレイカー"]},
        {"title": "명탐정코난", "kws": ["명탐정 코난", "Detective Conan", "名探偵コナン"]}
    ]
    if args.keyword:
        anim_id = get_or_create_animation("기타/요청")
        crawler = DucktemCrawler(args.keyword, anim_id)
        crawler.crawl_bunjang(); crawler.crawl_daangn(); crawler.crawl_dokidokigoods(); crawler.crawl_ittanstore(); crawler.crawl_heyprice(); crawler.crawl_bidbuy(); crawler.crawl_yahoo_jp(); crawler.crawl_ebay_us()
        crawler.save()
        return

    # 1. 굿즈 수집
    for g in genres:
        anim_id = get_or_create_animation(g['title'])
        for kw in g['kws']:
            c = DucktemCrawler(kw, anim_id)
            c.crawl_bunjang(); c.crawl_daangn(); c.crawl_dokidokigoods(); c.crawl_ittanstore(); c.crawl_heyprice(); c.crawl_bidbuy(); c.crawl_yahoo_jp(); c.crawl_ebay_us(); c.save()
            time.sleep(2)
        print(f"✅ {g['title']} 동기화 완료")

    # 2. 공식 이벤트 수집
    e = DucktemEventCrawler()
    e.crawl_animate_korea()
    e.crawl_hyundai_popups()
    e.save()
    print("📅 공식 이벤트 동기화 완료")

if __name__ == "__main__":
    main()

import requests
import json
import time
import re
import os
from typing import List, Dict, Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from bs4 import BeautifulSoup
from models.product import Product

class ShopeeCrawler:
    """Crawler để lấy dữ liệu sản phẩm từ Shopee sử dụng Selenium"""
    
    BASE_URL = "https://shopee.vn"
    COOKIES_FILE = "shopee_cookies.json"
    
    def __init__(self, headless: bool = True):
        """
        Khởi tạo crawler
        headless: True để chạy browser ẩn, False để hiển thị browser
        """
        self.headless = headless
        self.driver = None
        self._init_driver()
        self._load_cookies()
    
    def _init_driver(self):
        """Khởi tạo Selenium WebDriver"""
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless=new')  # Dùng headless mới
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Enable performance logging để intercept network requests
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            # Set window size
            self.driver.set_window_size(1920, 1080)
        except Exception as e:
            print(f"Lỗi khởi tạo Chrome driver: {e}")
            print("Đảm bảo đã cài đặt Chrome và ChromeDriver")
            raise
    
    def _load_cookies(self):
        """Load cookies từ file nếu có"""
        if os.path.exists(self.COOKIES_FILE):
            try:
                # Truy cập trang chủ trước
                self.driver.get(self.BASE_URL)
                time.sleep(2)
                
                with open(self.COOKIES_FILE, 'r', encoding='utf-8') as f:
                    cookies = json.load(f)
                    
                # Xóa cookies cũ trước
                self.driver.delete_all_cookies()
                
                # Load cookies mới
                loaded_count = 0
                for cookie in cookies:
                    try:
                        # Đảm bảo domain đúng
                        if 'domain' in cookie:
                            # Chỉnh domain nếu cần
                            if cookie['domain'].startswith('.'):
                                cookie['domain'] = cookie['domain'][1:]
                        self.driver.add_cookie(cookie)
                        loaded_count += 1
                    except Exception as e:
                        continue
                
                if loaded_count > 0:
                    print(f"✅ Đã load {loaded_count}/{len(cookies)} cookies từ file")
                    # Refresh để áp dụng cookies
                    self.driver.refresh()
                    time.sleep(2)
                    return True
            except Exception as e:
                print(f"⚠️ Không thể load cookies: {e}")
        return False
    
    def _save_cookies(self):
        """Lưu cookies vào file"""
        try:
            if self.driver:
                cookies = self.driver.get_cookies()
                with open(self.COOKIES_FILE, 'w', encoding='utf-8') as f:
                    json.dump(cookies, f, ensure_ascii=False, indent=2)
                print(f"✅ Đã lưu {len(cookies)} cookies vào {self.COOKIES_FILE}")
        except Exception as e:
            # Không in lỗi nếu driver đã đóng
            pass
    
    def close(self):
        """Đóng driver và lưu cookies"""
        if self.driver:
            try:
                # Lưu cookies trước khi đóng
                self._save_cookies()
            except:
                pass
            try:
                self.driver.quit()
            except:
                try:
                    self.driver.close()
                except:
                    pass
            self.driver = None
    
    def __del__(self):
        """Đóng driver khi hủy object"""
        self.close()
    
    def crawl_by_keyword(
        self, 
        keyword: str, 
        limit: int = 60,
        sort_by: str = "ctime"  # ctime, sales, price, pop
    ) -> List[Product]:
        """Crawl sản phẩm theo keyword"""
        products = []
        seen_product_ids = set()  # Để tránh trùng lặp
        
        # Map sort_by sang tham số URL của Shopee
        sort_map = {
            "ctime": "ctime",
            "sales": "sales",
            "price": "price",
            "pop": "pop"
        }
        sort_param = sort_map.get(sort_by, "ctime")
        
        try:
            # Tạo URL search
            search_url = f"{self.BASE_URL}/search?keyword={keyword.replace(' ', '%20')}"
            if sort_param != "ctime":
                search_url += f"&order={sort_param}"
            
            print(f"Đang truy cập: {search_url}")
            self.driver.get(search_url)
            time.sleep(5)  # Đợi trang load đầy đủ
            
            # Debug: Kiểm tra title và URL
            print(f"Title: {self.driver.title}")
            print(f"Current URL: {self.driver.current_url[:100]}...")
            
            # Kiểm tra xem có bị redirect đến trang CAPTCHA không
            if '/verify/captcha' in self.driver.current_url:
                print("\n" + "="*60)
                print("⚠️  SHOPEE YÊU CẦU GIẢI CAPTCHA!")
                print("="*60)
                
                if not self.headless:
                    print("\n📋 HƯỚNG DẪN:")
                    print("   1. Giải CAPTCHA trong browser đã mở")
                    print("   2. Sau khi giải xong và được redirect về trang search, nhấn Enter")
                    print("   3. Tool sẽ tiếp tục crawl dữ liệu")
                    print("\n⏳ Đang đợi bạn giải CAPTCHA...")
                    input("\n👉 Nhấn Enter sau khi giải CAPTCHA xong: ")
                    
                    # Kiểm tra lại URL
                    current_url = self.driver.current_url
                    if '/verify/captcha' not in current_url:
                        print("✅ Đã giải CAPTCHA thành công!")
                        # Reload trang search
                        self.driver.get(search_url)
                        time.sleep(5)
                    else:
                        print("❌ Vẫn còn ở trang CAPTCHA. Vui lòng giải lại.")
                        return products[:limit]
                else:
                    print("\n💡 CẦN GIẢI CAPTCHA!")
                    print("   Đang tự động chuyển sang chế độ hiển thị browser...")
                    
                    # Đóng browser headless và mở lại không headless
                    try:
                        self.driver.quit()
                    except:
                        pass
                    
                    # Mở lại với không headless
                    self.headless = False
                    chrome_options = Options()
                    chrome_options.add_argument('--no-sandbox')
                    chrome_options.add_argument('--disable-dev-shm-usage')
                    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    chrome_options.add_experimental_option('useAutomationExtension', False)
                    
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.driver.set_window_size(1920, 1080)
                    
                    # Load cookies lại
                    self._load_cookies()
                    
                    # Truy cập lại trang search
                    self.driver.get(search_url)
                    time.sleep(3)
                    
                    # Kiểm tra lại CAPTCHA
                    if '/verify/captcha' in self.driver.current_url:
                        print("\n📋 HƯỚNG DẪN GIẢI CAPTCHA:")
                        print("   1. Giải CAPTCHA trong browser đã mở")
                        print("   2. Sau khi giải xong, nhấn Enter ở đây")
                        print("   3. Tool sẽ tiếp tục crawl\n")
                        input("👉 Nhấn Enter sau khi giải CAPTCHA xong: ")
                        
                        # Kiểm tra lại
                        if '/verify/captcha' not in self.driver.current_url:
                            print("✅ Đã giải CAPTCHA thành công!")
                            self.driver.get(search_url)
                            time.sleep(5)
                        else:
                            print("❌ Vẫn còn ở trang CAPTCHA.")
                            return products[:limit]
            
            # Kiểm tra xem có bị redirect đến trang login không
            elif '/buyer/login' in self.driver.current_url or 'login' in self.driver.title.lower():
                print("⚠️ Shopee yêu cầu đăng nhập!")
                print("💡 Có 2 cách giải quyết:")
                print("   1. Chạy không headless (n) và đăng nhập thủ công trong browser")
                print("   2. Hoặc thử truy cập trực tiếp API với cookies hợp lệ")
                # Thử tiếp tục xem có thể crawl được không
                print("   Đang thử tiếp tục...")
            
            # Kiểm tra xem có CAPTCHA không (fallback)
            page_text = self.driver.page_source.lower()
            if 'captcha' in page_text or 'robot' in page_text:
                if '/verify/captcha' not in self.driver.current_url:
                    print("⚠️ Có thể có CAPTCHA hoặc verification!")
                    print("💡 Thử chạy không headless (n) để xem browser và giải CAPTCHA nếu có")
            
            # Debug: Lưu screenshot để kiểm tra
            if not self.headless:
                try:
                    self.driver.save_screenshot("shopee_debug.png")
                    print("Đã lưu screenshot: shopee_debug.png")
                except:
                    pass
            
            # Debug: Kiểm tra số lượng elements trên trang
            try:
                all_divs = self.driver.find_elements(By.TAG_NAME, "div")
                all_links = self.driver.find_elements(By.TAG_NAME, "a")
                print(f"Tổng số divs: {len(all_divs)}, Tổng số links: {len(all_links)}")
            except:
                pass
            
            # Thử lấy dữ liệu từ network requests (API calls)
            print("Đang lấy dữ liệu từ API...")
            api_products = self._crawl_from_api_keyword(keyword, limit, sort_by)
            for product in api_products:
                if product.product_id and product.product_id not in seen_product_ids:
                    products.append(product)
                    seen_product_ids.add(product.product_id)
            
            # Nếu chưa đủ, thử intercept network requests để lấy JSON
            if len(products) < limit:
                print(f"Đã lấy {len(products)} sản phẩm từ API, đang thử lấy từ network requests...")
                network_products = self._get_products_from_network_requests(keyword, limit - len(products))
                for product in network_products:
                    if product.product_id and product.product_id not in seen_product_ids:
                        products.append(product)
                        seen_product_ids.add(product.product_id)
            
            # Kiểm tra xem có đang ở trang login không
            if '/buyer/login' in self.driver.current_url:
                print("\n" + "="*60)
                print("⚠️  SHOPEE YÊU CẦU ĐĂNG NHẬP!")
                print("="*60)
                
                if not self.headless:
                    print("\n📋 HƯỚNG DẪN:")
                    print("   1. Đăng nhập trong browser đã mở")
                    print("   2. Sau khi đăng nhập thành công, nhấn Enter ở đây")
                    print("   3. Cookies sẽ được lưu tự động để lần sau không cần đăng nhập")
                    print("\n⏳ Đang đợi bạn đăng nhập...")
                    input("\n👉 Nhấn Enter sau khi đăng nhập xong: ")
                    
                    # Kiểm tra xem đã đăng nhập chưa
                    current_url = self.driver.current_url
                    if '/buyer/login' not in current_url:
                        print("✅ Đăng nhập thành công!")
                        # Lưu cookies
                        self._save_cookies()
                        # Reload trang search
                        self.driver.get(search_url)
                        time.sleep(5)
                    else:
                        print("❌ Vẫn chưa đăng nhập. Vui lòng thử lại.")
                        return products[:limit]
                else:
                    print("\n💡 PHÁT HIỆN CẦN ĐĂNG NHẬP!")
                    print("   Đang tự động chuyển sang chế độ hiển thị browser...")
                    print("   (Browser sẽ mở ra để bạn đăng nhập)\n")
                    
                    # Đóng browser headless và mở lại không headless
                    try:
                        self.driver.quit()
                    except:
                        pass
                    
                    # Mở lại với không headless
                    self.headless = False
                    chrome_options = Options()
                    chrome_options.add_argument('--no-sandbox')
                    chrome_options.add_argument('--disable-dev-shm-usage')
                    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
                    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
                    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    chrome_options.add_experimental_option('useAutomationExtension', False)
                    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
                    
                    self.driver = webdriver.Chrome(options=chrome_options)
                    self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
                    self.driver.set_window_size(1920, 1080)
                    
                    # Load cookies lại
                    self._load_cookies()
                    
                    # Truy cập lại trang search
                    self.driver.get(search_url)
                    time.sleep(3)
                    
                    # Kiểm tra lại
                    if '/buyer/login' in self.driver.current_url:
                        print("\n📋 HƯỚNG DẪN ĐĂNG NHẬP:")
                        print("   1. Đăng nhập trong browser đã mở")
                        print("   2. Sau khi đăng nhập thành công, nhấn Enter ở đây")
                        print("   3. Cookies sẽ được lưu tự động\n")
                        input("👉 Nhấn Enter sau khi đăng nhập xong: ")
                        
                        # Kiểm tra lại
                        if '/buyer/login' not in self.driver.current_url:
                            print("✅ Đăng nhập thành công!")
                            self._save_cookies()
                            self.driver.get(search_url)
                            time.sleep(5)
                        else:
                            print("❌ Vẫn chưa đăng nhập.")
                            return products[:limit]
                    else:
                        print("✅ Đã bypass login với cookies!")
            
            # Nếu vẫn chưa đủ, parse từ HTML bằng Selenium
            if len(products) < limit:
                print(f"Đã lấy {len(products)} sản phẩm, đang parse từ HTML...")
                
                # Kiểm tra lại xem có phải trang login không
                if '/buyer/login' in self.driver.current_url:
                    print("❌ Vẫn ở trang login. Vui lòng đăng nhập hoặc chạy không headless để đăng nhập.")
                    return products[:limit]
                
                # Đợi trang load hoàn toàn
                try:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                except:
                    pass
                
                # Đợi thêm để JavaScript render
                time.sleep(5)
                
                # Scroll để load thêm sản phẩm
                scroll_pause_time = 2
                scroll_count = 0
                max_scrolls = 5
                
                while len(products) < limit and scroll_count < max_scrolls:
                    # Scroll xuống từng phần
                    for i in range(3):
                        self.driver.execute_script(f"window.scrollTo(0, {i * 500});")
                        time.sleep(0.5)
                    
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(scroll_pause_time)
                    scroll_count += 1
                    
                    # Debug: In ra số lượng links tìm thấy
                    try:
                        all_links = self.driver.find_elements(By.CSS_SELECTOR, "a[href*='/product/']")
                        print(f"Tìm thấy {len(all_links)} links sản phẩm...")
                    except:
                        pass
                    
                    # Dùng Selenium để tìm elements trực tiếp
                    try:
                        # Thử nhiều selector khác nhau
                        selectors = [
                            "a[href*='/product/']",
                            "div[class*='shopee-search-item-result'] a",
                            "div[class*='col-xs-2-4'] a",
                            "div[data-sqe='item'] a",
                            "[class*='product-item'] a",
                            "[class*='search-result'] a"
                        ]
                        
                        for selector in selectors:
                            try:
                                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                print(f"Selector '{selector}': tìm thấy {len(elements)} elements")
                                
                                for elem in elements:
                                    if len(products) >= limit:
                                        break
                                    try:
                                        product = self._parse_product_from_selenium_element(elem)
                                        if product and product.product_id and product.product_id not in seen_product_ids:
                                            products.append(product)
                                            seen_product_ids.add(product.product_id)
                                            print(f"Đã parse sản phẩm: {product.name[:50]}...")
                                    except Exception as e:
                                        continue
                                
                                if len(products) >= limit:
                                    break
                            except Exception as e:
                                continue
                    except Exception as e:
                        print(f"Lỗi khi parse HTML: {e}")
                    
                    if len(products) >= limit:
                        break
                    
                    # Nếu không tìm thấy gì sau scroll đầu tiên, thử cách khác
                    if scroll_count == 1 and len(products) == 0:
                        print("Thử cách parse khác...")
                        # Thử parse từ HTML source
                        html = self.driver.page_source
                        soup = BeautifulSoup(html, 'html.parser')
                        
                        # Tìm tất cả links có chứa /product/
                        product_links = soup.find_all('a', href=re.compile(r'/product/\d+/\d+'))
                        print(f"Tìm thấy {len(product_links)} product links trong HTML")
                        
                        for link in product_links[:limit]:
                            try:
                                href = link.get('href', '')
                                match = re.search(r'/product/(\d+)/(\d+)', href)
                                if match:
                                    shop_id = match.group(1)
                                    product_id = match.group(2)
                                    
                                    if product_id not in seen_product_ids:
                                        # Tìm parent element để lấy thông tin
                                        parent = link.find_parent()
                                        name = ""
                                        price = 0
                                        
                                        if parent:
                                            name_elem = parent.find(string=re.compile(r'.+'))
                                            if name_elem:
                                                name = name_elem.strip()[:200]
                                        
                                        if not name:
                                            name = link.get_text(strip=True)[:200]
                                        
                                        if name:
                                            product = Product(
                                                name=name,
                                                price=price,
                                                original_price=None,
                                                commission_rate=None,
                                                sales_count=0,
                                                rating=None,
                                                shop_name="",
                                                shop_id=shop_id,
                                                product_id=product_id,
                                                category="",
                                                image_url="",
                                                product_url=f"{self.BASE_URL}{href}" if href.startswith('/') else href,
                                                location=""
                                            )
                                            products.append(product)
                                            seen_product_ids.add(product_id)
                                            print(f"Đã parse từ HTML: {name[:50]}...")
                            except:
                                continue
                        
                        if len(products) > 0:
                            break
            
        except Exception as e:
            print(f"Lỗi khi crawl keyword {keyword}: {e}")
            import traceback
            traceback.print_exc()
        
        print(f"Đã crawl được {len(products)} sản phẩm")
        return products[:limit]
    
    def _crawl_from_api_keyword(self, keyword: str, limit: int, sort_by: str) -> List[Product]:
        """Thử crawl từ API với cookies từ Selenium"""
        products = []
        try:
            # Đợi một chút để đảm bảo cookies đã được set
            time.sleep(2)
            
            # Lấy cookies từ Selenium
            cookies = self.driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'], domain=cookie.get('domain', '.shopee.vn'))
            
            # Lấy các headers từ browser
            user_agent = self.driver.execute_script("return navigator.userAgent;")
            
            # Encode keyword đúng cách
            encoded_keyword = keyword.replace(" ", "%20")
            try:
                import urllib.parse
                encoded_keyword = urllib.parse.quote(keyword)
            except:
                pass
            
            session.headers.update({
                'User-Agent': user_agent,
                'Referer': f'{self.BASE_URL}/search?keyword={encoded_keyword}',
                'Accept': 'application/json',
                'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
                'X-Requested-With': 'XMLHttpRequest',
                'X-API-Source': 'pc',
                'X-Shopee-Language': 'vi',
            })
            
            # Thử gọi API với cookies
            api_url = "https://shopee.vn/api/v4/search/search_items"
            page = 0
            
            while len(products) < limit:
                # Encode keyword đúng cách
                try:
                    import urllib.parse
                    encoded_keyword = urllib.parse.quote(keyword)
                except:
                    encoded_keyword = keyword.replace(" ", "%20")
                
                params = {
                    'by': sort_by,
                    'keyword': encoded_keyword,
                    'limit': min(60, limit - len(products)),
                    'newest': page * 60,
                    'order': 'desc' if sort_by != 'price' else 'asc',
                    'page_type': 'search',
                    'scenario': 'PAGE_GLOBAL_SEARCH',
                    'version': 2
                }
                
                # Encode params đúng cách
                try:
                    response = session.get(api_url, params=params, timeout=15)
                except UnicodeEncodeError:
                    # Fallback: encode manually
                    import urllib.parse
                    query_string = urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
                    full_url = f"{api_url}?{query_string}"
                    response = session.get(full_url, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    if not items:
                        break
                    for item in items:
                        if len(products) >= limit:
                            break
                        product = self._parse_product_from_api(item)
                        if product:
                            products.append(product)
                    page += 1
                    time.sleep(1)
                else:
                    # Nếu bị 403, thử intercept network requests từ Selenium
                    if response.status_code == 403:
                        print("API bị chặn, sẽ parse từ HTML...")
                    break
        except Exception as e:
            print(f"Lỗi khi crawl từ API: {e}")
        
        return products
    
    def _get_products_from_network_requests(self, keyword: str, limit: int) -> List[Product]:
        """Lấy dữ liệu từ network requests bằng Chrome DevTools Protocol"""
        products = []
        try:
            # Lấy performance logs để xem network requests
            logs = self.driver.get_log('performance')
            
            for log in logs:
                try:
                    message = json.loads(log['message'])['message']
                    if message['method'] == 'Network.responseReceived':
                        url = message['params']['response']['url']
                        if 'search_items' in url or 'search/search_items' in url:
                            request_id = message['params']['requestId']
                            # Lấy response body
                            try:
                                response_body = self.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': request_id})
                                if response_body and 'body' in response_body:
                                    data = json.loads(response_body['body'])
                                    if 'items' in data:
                                        for item in data['items'][:limit]:
                                            product = self._parse_product_from_api(item)
                                            if product:
                                                products.append(product)
                            except:
                                pass
                except:
                    continue
            
            # Nếu không lấy được từ logs, thử intercept bằng JavaScript
            if len(products) == 0:
                # Scroll để trigger API calls
                for i in range(2):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                
                # Thử lấy từ window object
                try:
                    script = """
                    return window.__NEXT_DATA__ || window.__INITIAL_STATE__ || window.__SHOPEE_DATA__ || {};
                    """
                    data = self.driver.execute_script(script)
                    if isinstance(data, dict):
                        # Tìm items trong data
                        def find_items(obj, path=""):
                            if isinstance(obj, dict):
                                if 'items' in obj and isinstance(obj['items'], list):
                                    return obj['items']
                                for key, value in obj.items():
                                    result = find_items(value, f"{path}.{key}")
                                    if result:
                                        return result
                            elif isinstance(obj, list):
                                for item in obj:
                                    result = find_items(item, path)
                                    if result:
                                        return result
                            return None
                        
                        items = find_items(data)
                        if items:
                            for item in items[:limit]:
                                product = self._parse_product_from_api(item)
                                if product:
                                    products.append(product)
                except Exception as e:
                    print(f"Lỗi khi lấy từ window object: {e}")
                
        except Exception as e:
            print(f"Lỗi khi lấy từ network: {e}")
        
        return products[:limit]
    
    def _parse_product_from_selenium_element(self, element) -> Optional[Product]:
        """Parse sản phẩm từ Selenium WebElement"""
        try:
            # Lấy href để extract product_id
            href = element.get_attribute('href')
            
            # Nếu element không phải là link, tìm link bên trong
            if not href or '/product/' not in href:
                try:
                    # Thử tìm link trong element hoặc parent
                    link_elem = element.find_element(By.CSS_SELECTOR, "a[href*='/product/']")
                    href = link_elem.get_attribute('href')
                except:
                    try:
                        # Thử tìm trong parent
                        parent = element.find_element(By.XPATH, "./..")
                        link_elem = parent.find_element(By.CSS_SELECTOR, "a[href*='/product/']")
                        href = link_elem.get_attribute('href')
                    except:
                        return None
            
            if not href or '/product/' not in href:
                return None
            
            # Extract shop_id và product_id
            match = re.search(r'/product/(\d+)/(\d+)', href)
            if not match:
                return None
            
            shop_id = match.group(1)
            product_id = match.group(2)
            product_url = f"{self.BASE_URL}{href}" if href.startswith('/') else href
            
            # Lấy tên sản phẩm
            name = ""
            try:
                name_elem = element.find_element(By.CSS_SELECTOR, "[class*='name'], [class*='title'], [class*='product-name']")
                name = name_elem.text.strip()
            except:
                try:
                    name = element.find_element(By.TAG_NAME, "a").text.strip()
                except:
                    pass
            
            if not name:
                return None
            
            # Lấy giá
            price = 0
            try:
                price_elem = element.find_element(By.CSS_SELECTOR, "[class*='price'], [class*='final-price']")
                price_text = price_elem.text.strip()
                price_match = re.search(r'(\d+(?:\.\d+)?)', price_text.replace('.', '').replace(',', ''))
                if price_match:
                    price = float(price_match.group(1))
            except:
                pass
            
            # Lấy hình ảnh
            image_url = ""
            try:
                img_elem = element.find_element(By.CSS_SELECTOR, "img")
                image_url = img_elem.get_attribute('src') or img_elem.get_attribute('data-src') or ""
                if image_url and not image_url.startswith('http'):
                    image_url = f"https:{image_url}" if image_url.startswith('//') else f"https://{image_url}"
            except:
                pass
            
            # Lấy số lượng bán
            sales_count = 0
            try:
                text = element.text
                sold_match = re.search(r'đã\s*bán[:\s]*(\d+(?:\.\d+)?[kK]?)', text, re.IGNORECASE)
                if sold_match:
                    sold_num = sold_match.group(1).lower()
                    if 'k' in sold_num:
                        sales_count = int(float(sold_num.replace('k', '')) * 1000)
                    else:
                        sales_count = int(float(sold_num))
            except:
                pass
            
            return Product(
                name=name,
                price=price,
                original_price=None,
                commission_rate=None,
                sales_count=sales_count,
                rating=None,
                shop_name="",
                shop_id=shop_id,
                product_id=product_id,
                category="",
                image_url=image_url,
                product_url=product_url,
                location=""
            )
        except Exception as e:
            return None
    
    def crawl_by_category(
        self,
        category_id: int,
        limit: int = 60,
        sort_by: str = "ctime"
    ) -> List[Product]:
        """Crawl sản phẩm theo category"""
        products = []
        
        try:
            category_url = f"{self.BASE_URL}/api/v4/search/search_items"
            
            # Lấy cookies từ Selenium
            cookies = self.driver.get_cookies()
            session = requests.Session()
            for cookie in cookies:
                session.cookies.set(cookie['name'], cookie['value'])
            
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': f'{self.BASE_URL}/',
                'Accept': 'application/json',
            })
            
            page = 0
            while len(products) < limit:
                params = {
                    'by': sort_by,
                    'categoryids': category_id,
                    'limit': min(60, limit - len(products)),
                    'newest': page * 60,
                    'order': 'desc' if sort_by != 'price' else 'asc',
                    'page_type': 'search',
                    'scenario': 'PAGE_CATEGORY',
                    'version': 2
                }
                
                response = session.get(category_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    items = data.get('items', [])
                    if not items:
                        break
                    for item in items:
                        if len(products) >= limit:
                            break
                        product = self._parse_product_from_api(item)
                        if product:
                            products.append(product)
                    page += 1
                    time.sleep(1)
                else:
                    break
        except Exception as e:
            print(f"Lỗi khi crawl category {category_id}: {e}")
        
        return products[:limit]
    
    def crawl_by_shop(
        self,
        shop_id: str,
        limit: int = 60
    ) -> List[Product]:
        """Crawl sản phẩm theo shop"""
        products = []
        
        try:
            shop_url = f"{self.BASE_URL}/shop/{shop_id}"
            print(f"Đang truy cập shop: {shop_url}")
            self.driver.get(shop_url)
            time.sleep(3)
            
            # Scroll và load sản phẩm
            scroll_pause_time = 1
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            while len(products) < limit:
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause_time)
                
                html = self.driver.page_source
                soup = BeautifulSoup(html, 'html.parser')
                
                # Parse sản phẩm từ HTML
                product_elements = soup.find_all('div', class_=re.compile(r'col-xs-2-4|shopee-search-item'))
                for element in product_elements:
                    if len(products) >= limit:
                        break
                    product = self._parse_product_from_html(element, shop_id=shop_id)
                    if product and product not in products:
                        products.append(product)
                
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
                
                if len(products) >= limit:
                    break
        except Exception as e:
            print(f"Lỗi khi crawl shop {shop_id}: {e}")
        
        return products[:limit]
    
    def _parse_product_from_api(self, item: Dict) -> Optional[Product]:
        """Parse sản phẩm từ API response"""
        try:
            item_basic = item.get('item_basic', {})
            
            if not item_basic:
                return None
            
            price = item_basic.get('price', 0) / 100000
            original_price = item_basic.get('price_before_discount', 0) / 100000
            shop_id = str(item_basic.get('shopid', ''))
            shop_name = item_basic.get('shop_name', '')
            sales_count = item_basic.get('historical_sold', 0)
            rating = item_basic.get('item_rating', {}).get('rating_star', 0)
            name = item_basic.get('name', '')
            product_id = str(item_basic.get('itemid', ''))
            image_url = f"https://cf.shopee.vn/file/{item_basic.get('image', '')}"
            product_url = f"https://shopee.vn/product/{shop_id}/{product_id}"
            category = str(item_basic.get('catid', ''))
            location = item_basic.get('shop_location', '')
            
            return Product(
                name=name,
                price=price,
                original_price=original_price if original_price > price else None,
                commission_rate=None,
                sales_count=sales_count,
                rating=rating,
                shop_name=shop_name,
                shop_id=shop_id,
                product_id=product_id,
                category=category,
                image_url=image_url,
                product_url=product_url,
                location=location
            )
        except Exception as e:
            return None
    
    def _parse_product_from_html(self, element, shop_id: Optional[str] = None) -> Optional[Product]:
        """Parse sản phẩm từ HTML element"""
        try:
            # Tìm link sản phẩm trước (quan trọng nhất)
            link_elem = element.find('a', href=re.compile(r'/product/'))
            if not link_elem:
                return None
            
            href = link_elem.get('href', '')
            if not href:
                return None
            
            product_url = f"{self.BASE_URL}{href}" if href.startswith('/') else href
            
            # Extract shop_id và product_id từ URL
            match = re.search(r'/product/(\d+)/(\d+)', href)
            if not match:
                return None
            
            shop_id = match.group(1)
            product_id = match.group(2)
            
            # Tìm tên sản phẩm - thử nhiều selector
            name = ""
            name_selectors = [
                'div[class*="name"]',
                'div[class*="product-name"]',
                'div[class*="title"]',
                'a[href*="/product/"]'
            ]
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text(strip=True)
                    if name:
                        break
            
            if not name:
                name = link_elem.get_text(strip=True)
            
            if not name:
                return None
            
            # Tìm giá - thử nhiều selector
            price = 0
            price_selectors = [
                'span[class*="price"]',
                'div[class*="price"]',
                '[class*="final-price"]',
                '[class*="current-price"]'
            ]
            for selector in price_selectors:
                price_elem = element.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Extract số từ giá
                    price_match = re.search(r'(\d+(?:\.\d+)?)', price_text.replace('.', '').replace(',', ''))
                    if price_match:
                        price = float(price_match.group(1))
                        break
            
            # Tìm hình ảnh
            img_elem = element.find('img')
            image_url = ""
            if img_elem:
                image_url = img_elem.get('src', '') or img_elem.get('data-src', '')
                if image_url and not image_url.startswith('http'):
                    image_url = f"https:{image_url}" if image_url.startswith('//') else f"https://{image_url}"
            
            # Tìm số lượng bán
            sales_count = 0
            sold_text = element.get_text()
            sold_match = re.search(r'đã\s*bán[:\s]*(\d+(?:\.\d+)?[kK]?)', sold_text, re.IGNORECASE)
            if sold_match:
                sold_num = sold_match.group(1).lower()
                if 'k' in sold_num:
                    sales_count = int(float(sold_num.replace('k', '')) * 1000)
                else:
                    sales_count = int(float(sold_num))
            
            # Tìm rating
            rating = None
            rating_elem = element.find(string=re.compile(r'\d+\.\d+'))
            if rating_elem:
                rating_match = re.search(r'(\d+\.\d+)', rating_elem)
                if rating_match:
                    rating = float(rating_match.group(1))
            
            return Product(
                name=name,
                price=price,
                original_price=None,
                commission_rate=None,
                sales_count=sales_count,
                rating=rating,
                shop_name="",
                shop_id=shop_id,
                product_id=product_id,
                category="",
                image_url=image_url,
                product_url=product_url,
                location=""
            )
        except Exception as e:
            return None

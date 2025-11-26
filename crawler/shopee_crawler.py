import requests
import json
import time
from typing import List, Dict, Optional
from fake_useragent import UserAgent
from models.product import Product

class ShopeeCrawler:
    """Crawler để lấy dữ liệu sản phẩm từ Shopee"""
    
    BASE_URL = "https://shopee.vn/api/v4"
    SEARCH_URL = f"{BASE_URL}/search/search_items"
    
    def __init__(self):
        self.session = requests.Session()
        self.ua = UserAgent()
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Referer': 'https://shopee.vn/',
            'Accept': 'application/json',
        })
    
    def crawl_by_keyword(
        self, 
        keyword: str, 
        limit: int = 60,
        sort_by: str = "ctime"  # ctime, sales, price, pop
    ) -> List[Product]:
        """Crawl sản phẩm theo keyword"""
        products = []
        page = 0
        
        while len(products) < limit:
            params = {
                'by': sort_by,
                'keyword': keyword,
                'limit': min(60, limit - len(products)),
                'newest': page * 60,
                'order': 'desc' if sort_by != 'price' else 'asc',
                'page_type': 'search',
                'scenario': 'PAGE_GLOBAL_SEARCH',
                'version': 2
            }
            
            try:
                response = self.session.get(self.SEARCH_URL, params=params)
                data = response.json()
                
                if 'items' not in data:
                    break
                    
                for item in data['items']:
                    product = self._parse_product(item)
                    if product:
                        products.append(product)
                
                if len(data['items']) < 60:
                    break
                    
                page += 1
                time.sleep(1)  # Tránh bị block
                
            except Exception as e:
                print(f"Lỗi khi crawl keyword {keyword}: {e}")
                break
        
        return products
    
    def crawl_by_category(
        self,
        category_id: int,
        limit: int = 60,
        sort_by: str = "ctime"
    ) -> List[Product]:
        """Crawl sản phẩm theo category"""
        products = []
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
            
            try:
                response = self.session.get(self.SEARCH_URL, params=params)
                data = response.json()
                
                if 'items' not in data:
                    break
                    
                for item in data['items']:
                    product = self._parse_product(item)
                    if product:
                        products.append(product)
                
                if len(data['items']) < 60:
                    break
                    
                page += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"Lỗi khi crawl category {category_id}: {e}")
                break
        
        return products
    
    def crawl_by_shop(
        self,
        shop_id: str,
        limit: int = 60
    ) -> List[Product]:
        """Crawl sản phẩm theo shop"""
        products = []
        page = 0
        
        shop_url = f"{self.BASE_URL}/product/get_shop_items"
        
        while len(products) < limit:
            params = {
                'limit': min(60, limit - len(products)),
                'offset': page * 60,
                'shopid': shop_id,
                'sort_soldout': 0,
                'version': 2
            }
            
            try:
                response = self.session.get(shop_url, params=params)
                data = response.json()
                
                if 'items' not in data:
                    break
                    
                for item in data['items']:
                    product = self._parse_product(item, shop_id=shop_id)
                    if product:
                        products.append(product)
                
                if len(data['items']) < 60:
                    break
                    
                page += 1
                time.sleep(1)
                
            except Exception as e:
                print(f"Lỗi khi crawl shop {shop_id}: {e}")
                break
        
        return products
    
    def _parse_product(self, item: Dict, shop_id: Optional[str] = None) -> Optional[Product]:
        """Parse dữ liệu sản phẩm từ API response"""
        try:
            item_basic = item.get('item_basic', {})
            
            # Lấy giá
            price = item_basic.get('price', 0) / 100000  # Shopee trả về giá * 100000
            original_price = item_basic.get('price_before_discount', 0) / 100000
            
            # Lấy thông tin shop
            shop_id = shop_id or str(item_basic.get('shopid', ''))
            shop_name = item_basic.get('shop_name', '')
            
            # Lấy số lượng bán
            sales_count = item_basic.get('historical_sold', 0)
            
            # Lấy rating
            rating = item_basic.get('item_rating', {}).get('rating_star', 0)
            
            # Lấy tên sản phẩm
            name = item_basic.get('name', '')
            
            # Lấy ID sản phẩm
            product_id = str(item_basic.get('itemid', ''))
            
            # Lấy hình ảnh
            image_url = f"https://cf.shopee.vn/file/{item_basic.get('image', '')}"
            
            # Tạo URL sản phẩm
            product_url = f"https://shopee.vn/product/{shop_id}/{product_id}"
            
            # Lấy category
            category = item_basic.get('catid', '')
            
            # Lấy location
            location = item_basic.get('shop_location', '')
            
            # Lấy commission rate (cần parse từ thông tin khác hoặc API khác)
            commission_rate = None  # Cần implement thêm
            
            product = Product(
                name=name,
                price=price,
                original_price=original_price if original_price > price else None,
                commission_rate=commission_rate,
                sales_count=sales_count,
                rating=rating,
                shop_name=shop_name,
                shop_id=shop_id,
                product_id=product_id,
                category=str(category),
                image_url=image_url,
                product_url=product_url,
                location=location
            )
            
            return product
            
        except Exception as e:
            print(f"Lỗi khi parse product: {e}")
            return None



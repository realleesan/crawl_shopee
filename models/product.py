from dataclasses import dataclass
from typing import Optional

@dataclass
class Product:
    """Model đại diện cho sản phẩm Shopee"""
    name: str
    price: float
    original_price: Optional[float] = None
    commission_rate: Optional[float] = None  # % hoa hồng
    sales_count: int = 0  # Lượt bán
    rating: Optional[float] = None
    shop_name: str = ""
    shop_id: str = ""
    product_id: str = ""
    category: str = ""
    image_url: str = ""
    product_url: str = ""
    location: str = ""
    
    def to_dict(self):
        """Chuyển đổi sang dictionary"""
        return {
            'name': self.name,
            'price': self.price,
            'original_price': self.original_price,
            'commission_rate': self.commission_rate,
            'sales_count': self.sales_count,
            'rating': self.rating,
            'shop_name': self.shop_name,
            'product_id': self.product_id,
            'category': self.category,
            'image_url': self.image_url,
            'product_url': self.product_url,
            'location': self.location
        }



from typing import List
from models.product import Product

class ProductSorter:
    """Class để sắp xếp sản phẩm"""
    
    @staticmethod
    def sort_by_commission(products: List[Product], reverse: bool = True) -> List[Product]:
        """Sắp xếp theo % hoa hồng"""
        return sorted(
            products,
            key=lambda p: p.commission_rate if p.commission_rate else 0,
            reverse=reverse
        )
    
    @staticmethod
    def sort_by_price(products: List[Product], reverse: bool = False) -> List[Product]:
        """Sắp xếp theo giá (mặc định tăng dần)"""
        return sorted(products, key=lambda p: p.price, reverse=reverse)
    
    @staticmethod
    def sort_by_sales(products: List[Product], reverse: bool = True) -> List[Product]:
        """Sắp xếp theo lượt bán"""
        return sorted(products, key=lambda p: p.sales_count, reverse=reverse)
    
    @staticmethod
    def sort_by_rating(products: List[Product], reverse: bool = True) -> List[Product]:
        """Sắp xếp theo đánh giá"""
        return sorted(
            products,
            key=lambda p: p.rating if p.rating else 0,
            reverse=reverse
        )



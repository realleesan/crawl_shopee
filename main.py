import json
import pandas as pd
from crawler.shopee_crawler import ShopeeCrawler
from filters.sorter import ProductSorter

def main():
    crawler = None
    try:
        print("=== TOOL CRAWL DỮ LIỆU SHOPEE ===\n")
        print("📌 LƯU Ý: Shopee yêu cầu đăng nhập để crawl dữ liệu.")
        print("   Lần đầu tiên cần đăng nhập, cookies sẽ được lưu tự động.\n")
        
        # Hỏi có muốn chạy headless không
        headless_choice = input("Chạy browser ẩn? (y/n, mặc định: y): ").lower()
        headless = headless_choice != 'n'
        
        if headless:
            print("\n⚠️  Chạy headless có thể không đăng nhập được.")
            print("   Nếu gặp lỗi, hãy chạy lại với 'n' để hiển thị browser.\n")
        
        crawler = ShopeeCrawler(headless=headless)
        sorter = ProductSorter()
        
        print("\n1. Crawl theo keyword")
        print("2. Crawl theo category")
        print("3. Crawl theo shop")
        
        choice = input("\nChọn phương thức crawl (1/2/3): ")
        
        products = []
        
        if choice == "1":
            keyword = input("Nhập keyword: ")
            limit = int(input("Số lượng sản phẩm cần crawl: "))
            products = crawler.crawl_by_keyword(keyword, limit=limit)
            
        elif choice == "2":
            category_id = int(input("Nhập category ID: "))
            limit = int(input("Số lượng sản phẩm cần crawl: "))
            products = crawler.crawl_by_category(category_id, limit=limit)
            
        elif choice == "3":
            shop_id = input("Nhập shop ID: ")
            limit = int(input("Số lượng sản phẩm cần crawl: "))
            products = crawler.crawl_by_shop(shop_id, limit=limit)
        
        if not products:
            print("Không tìm thấy sản phẩm nào!")
            return
        
        # Sắp xếp
        print("\n=== SẮP XẾP ===")
        print("1. Theo % hoa hồng")
        print("2. Theo giá tiền")
        print("3. Theo lượt bán")
        print("4. Theo rating")
        
        sort_choice = input("\nChọn cách sắp xếp (1/2/3/4): ")
        
        if sort_choice == "1":
            products = sorter.sort_by_commission(products)
        elif sort_choice == "2":
            reverse = input("Sắp xếp giảm dần? (y/n): ").lower() == 'y'
            products = sorter.sort_by_price(products, reverse=reverse)
        elif sort_choice == "3":
            products = sorter.sort_by_sales(products)
        elif sort_choice == "4":
            products = sorter.sort_by_rating(products)
        
        # Xuất dữ liệu
        print("\n=== XUẤT DỮ LIỆU ===")
        print("1. JSON")
        print("2. Excel")
        
        export_choice = input("\nChọn định dạng xuất (1/2): ")
        
        if export_choice == "1":
            filename = input("Tên file JSON: ")
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump([p.to_dict() for p in products], f, ensure_ascii=False, indent=2)
            print(f"Đã lưu vào {filename}")
            
        elif export_choice == "2":
            filename = input("Tên file Excel: ")
            df = pd.DataFrame([p.to_dict() for p in products])
            df.to_excel(filename, index=False, engine='openpyxl')
            print(f"Đã lưu vào {filename}")
        
        print(f"\nĐã crawl được {len(products)} sản phẩm!")
    
    except KeyboardInterrupt:
        print("\n\nĐã hủy bởi người dùng.")
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Đóng browser an toàn
        if crawler:
            try:
                crawler.close()
                print("Đã đóng browser.")
            except Exception as e:
                pass

if __name__ == "__main__":
    main()



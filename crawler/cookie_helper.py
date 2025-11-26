"""
Helper để import cookies từ Chrome profile đã đăng nhập Shopee
"""
import json
import os
import sqlite3
import shutil
from pathlib import Path

def get_chrome_cookies():
    """Lấy cookies từ Chrome profile"""
    cookies = []
    
    # Đường dẫn Chrome profile trên Windows
    chrome_paths = [
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Default\Cookies"),
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\User Data\Profile 1\Cookies"),
    ]
    
    for cookies_path in chrome_paths:
        if os.path.exists(cookies_path):
            try:
                # Copy file cookies để tránh lock
                temp_cookies = cookies_path + "_temp"
                shutil.copy2(cookies_path, temp_cookies)
                
                # Kết nối database
                conn = sqlite3.connect(temp_cookies)
                cursor = conn.cursor()
                
                # Lấy cookies của shopee.vn
                cursor.execute("""
                    SELECT name, value, host_key, path, expires_utc, is_secure, is_httponly
                    FROM cookies
                    WHERE host_key LIKE '%shopee.vn%'
                """)
                
                for row in cursor.fetchall():
                    cookie = {
                        'name': row[0],
                        'value': row[1],
                        'domain': row[2],
                        'path': row[3] if row[3] else '/',
                        'expiry': row[4] if row[4] else None,
                        'secure': bool(row[5]),
                        'httpOnly': bool(row[6])
                    }
                    cookies.append(cookie)
                
                conn.close()
                os.remove(temp_cookies)
                
                if cookies:
                    print(f"✅ Đã tìm thấy {len(cookies)} cookies từ Chrome profile")
                    return cookies
                    
            except Exception as e:
                print(f"⚠️ Không thể đọc cookies từ {cookies_path}: {e}")
                if os.path.exists(temp_cookies):
                    try:
                        os.remove(temp_cookies)
                    except:
                        pass
    
    return cookies

def save_cookies_to_file(cookies, filename="shopee_cookies.json"):
    """Lưu cookies vào file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        print(f"✅ Đã lưu {len(cookies)} cookies vào {filename}")
        return True
    except Exception as e:
        print(f"❌ Lỗi khi lưu cookies: {e}")
        return False

if __name__ == "__main__":
    print("=== IMPORT COOKIES TỪ CHROME ===\n")
    print("Đang tìm cookies từ Chrome profile...")
    
    cookies = get_chrome_cookies()
    
    if cookies:
        save_cookies_to_file(cookies)
        print("\n✅ Hoàn thành! Cookies đã được lưu vào shopee_cookies.json")
        print("Bây giờ bạn có thể chạy: py main.py")
    else:
        print("\n❌ Không tìm thấy cookies Shopee trong Chrome.")
        print("\n💡 HƯỚNG DẪN:")
        print("   1. Mở Chrome và đăng nhập vào Shopee")
        print("   2. Đảm bảo Chrome đã đóng hoàn toàn")
        print("   3. Chạy lại script này: py crawler/cookie_helper.py")


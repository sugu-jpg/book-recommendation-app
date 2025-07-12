import requests
from typing import List, Dict, Any
import re

class GoogleBooksClient:
    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
    
    def detect_volume_number(self, title: str) -> tuple[bool, int]:
        """巻数を検出（1巻かどうか、巻数）"""
        # 1巻のパターン
        volume_one_patterns = [
            r'^(.+?)\s*1$',           # タイトル末尾が1
            r'^(.+?)\s*第1巻',        # 第1巻
            r'^(.+?)\s*1巻',          # 1巻
            r'^(.+?)\s*一巻',         # 一巻
            r'vol\.?\s*1$',           # Vol.1
            r'#1$',                   # #1
            r'\s1\s*$'               # 末尾スペース1
        ]
        
        # 他の巻のパターン
        volume_patterns = [
            r'第?(\d+)巻',            # 第n巻、n巻
            r'vol\.?\s*(\d+)',        # Vol.n
            r'#(\d+)$',               # #n
            r'\s(\d+)\s*$'           # 末尾の数字
        ]
        
        title_lower = title.lower()
        
        # 1巻チェック
        is_volume_one = any(re.search(pattern, title_lower) for pattern in volume_one_patterns)
        
        # 巻数抽出
        volume_num = 1  # デフォルト
        for pattern in volume_patterns:
            match = re.search(pattern, title_lower)
            if match:
                volume_num = int(match.group(1))
                break
        
        return is_volume_one, volume_num
    
    def extract_base_title(self, title: str) -> str:
        """ベースタイトルを抽出（巻数除去）"""
        # 巻数パターンを除去
        patterns_to_remove = [
            r'\s*第?\d+巻\s*',
            r'\s*\d+巻?\s*',
            r'\s*vol\.?\s*\d+\s*',
            r'\s*#\d+\s*',
            r'\s*\(\d+\)\s*',
            r'\s*\d+\s*$'  # 末尾の数字
        ]
        
        cleaned = title
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def calculate_recommendation_score(self, book: Dict[Any, Any], prefer_volume_one: bool = True) -> float:
        """レコメンド用スコア計算"""
        score = 0.0
        title = book.get('title', '')
        
        # 1巻判定
        is_volume_one, volume_num = self.detect_volume_number(title)
        
        if prefer_volume_one:
            if is_volume_one:
                score += 1000  # 1巻は大幅加点
            elif volume_num <= 3:
                score += 100   # 初期巻は少し加点
            else:
                score -= volume_num * 10  # 巻数が多いほど減点
        
        # その他の要素
        if book.get('authors'):
            score += 50
        if book.get('image'):
            score += 30
        if book.get('rating', 0) > 0:
            score += book.get('rating', 0) * 20
        
        # 不要なバリエーションの減点
        variants = ['完全版', 'カラー版', '新装版', '4コマ', 'ショート', 'アンソロジー', '番外編']
        if any(variant in title for variant in variants):
            score -= 200
        
        return score
    
    def find_volume_one_alternative(self, books: List[Dict[Any, Any]], target_book: Dict[Any, Any]) -> Dict[Any, Any]:
        """同じシリーズの1巻を探す"""
        target_title = target_book.get('title', '')
        target_base = self.extract_base_title(target_title)
        
        # 同じベースタイトルの1巻を探す
        for book in books:
            book_title = book.get('title', '')
            book_base = self.extract_base_title(book_title)
            is_volume_one, _ = self.detect_volume_number(book_title)
            
            # ベースタイトルが似ていて、1巻の場合
            if (len(target_base) > 2 and len(book_base) > 2 and 
                (target_base.lower() in book_base.lower() or 
                 book_base.lower() in target_base.lower()) and 
                is_volume_one):
                return book
        
        return target_book  # 1巻が見つからない場合は元の本を返す
    
    def search_books_with_filters(self, query: str, content_type: str, max_results: int = 10) -> List[Dict[Any, Any]]:
        """シンプルな検索（エラー対策）"""
        try:
            # シンプルなクエリに変更
            search_query = query
            
            params = {
                "q": search_query,
                "maxResults": max_results * 2,
                "langRestrict": "ja"
            }
            
            print(f"[DEBUG] Google Books APIクエリ: {search_query}")
            
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if not data.get("items"):
                print(f"[DEBUG] 検索結果なし")
                return []
            
            books = []
            for item in data.get("items", []):
                volume_info = item.get("volumeInfo", {})
                book = {
                    "google_id": item.get("id", ""),
                    "title": volume_info.get("title", ""),
                    "authors": volume_info.get("authors", []),
                    "description": volume_info.get("description", ""),
                    "image": volume_info.get("imageLinks", {}).get("thumbnail", ""),
                    "categories": volume_info.get("categories", []),
                    "rating": volume_info.get("averageRating", 0),
                    "published_date": volume_info.get("publishedDate", "")
                }
                books.append(book)
            
            print(f"[DEBUG] 取得した本の数: {len(books)}")
            return books[:max_results]
        
        except Exception as e:
            print(f"Google Books error: {e}")
            return []
    
    def search_books(self, query: str, max_results: int = 10) -> List[Dict[Any, Any]]:
        """基本検索"""
        return self.search_books_with_filters(query, "general", max_results)

google_books = GoogleBooksClient()

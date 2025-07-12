import requests
from typing import List, Dict, Any, Tuple, Set
import re
from collections import Counter

class GoogleBooksClient:
    def __init__(self):
        self.base_url = "https://www.googleapis.com/books/v1/volumes"
    
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

class TextAnalyzer:
    def __init__(self):
        # 実際の漫画タイトルから推測できる実用的なキーワード
        self.manga_genre_mapping = {
            # スポーツ漫画
            'スポーツ': ['ハイキュー', 'スラムダンク', 'slam dunk', 'テニス', 'サッカー', 'バスケ', '野球', 'メダリスト', 'アオのハコ', 'バレー'],
            
            # バトル・アクション
            'バトル': ['ヒーロー', 'hero', 'アカデミア', '呪術', '廻戦', '進撃', '巨人', 'ワンパン', 'マン', 'dragon ball', 'ドラゴンボール'],
            
            # 冒険・ファンタジー
            '冒険': ['piece', 'ピース', 'トリコ', '冒険', 'ファンタジー', '魔法', '異世界'],
            
            # 恋愛・日常
            '恋愛': ['恋', '恋愛', 'ロマンス', '着せ替え', '人形', '花', '咲く'],
            
            # ホラー・サスペンス
            'ホラー': ['鬼', '悪魔', 'デーモン', 'ホラー', '恐怖'],
            
            # SF・近未来
            'SF': ['サイボーグ', 'ロボット', 'SF', '未来', '宇宙'],
            
            # 学園・青春
            '学園': ['学園', '学校', '高校', 'スクール', '青春']
        }
        
        # 著者マッピング（よく知られた作品と著者）
        self.known_works = {
            'ワンピース': '尾田栄一郎',
            'one piece': '尾田栄一郎', 
            'ナルト': '岸本斉史',
            'naruto': '岸本斉史',
            'ドラゴンボール': '鳥山明',
            'スラムダンク': '井上雄彦',
            'slam dunk': '井上雄彦',
            'ハイキュー': '古舘春一',
            '進撃の巨人': '諫山創',
            '呪術廻戦': '芥見下々',
            '僕のヒーローアカデミア': '堀越耕平',
            'ヒーローアカデミア': '堀越耕平',
            'トリコ': '島袋光年',
            'ワンパンマン': 'ONE',
            '鋼の錬金術師': '荒川弘'
        }
    
    def extract_genres_from_titles(self, user_books: List[Dict[Any, Any]]) -> List[str]:
        """タイトルからジャンルを推測"""
        found_genres = []
        
        print(f"[DEBUG] ジャンル抽出開始")
        
        for book in user_books:
            title = book.get('title', '').lower()
            print(f"[DEBUG] 分析中: {title}")
            
            book_genres = []
            for genre, keywords in self.manga_genre_mapping.items():
                for keyword in keywords:
                    if keyword.lower() in title:
                        found_genres.append(genre)
                        book_genres.append(genre)
                        break
            
            print(f"[DEBUG] 見つかったジャンル: {book_genres}")
        
        # 頻度順でソート
        genre_counter = Counter(found_genres)
        result = [genre for genre, count in genre_counter.most_common(3)]
        print(f"[DEBUG] 最終ジャンル: {result}")
        return result
    
    def extract_authors_from_known_works(self, user_books: List[Dict[Any, Any]]) -> List[str]:
        """既知の作品から著者を推測"""
        found_authors = []
        
        print(f"[DEBUG] 著者推測開始")
        
        for book in user_books:
            title = book.get('title', '').lower()
            print(f"[DEBUG] 著者分析中: {title}")
            
            found_author = None
            for work, author in self.known_works.items():
                if work.lower() in title:
                    found_authors.append(author)
                    found_author = author
                    break
            
            print(f"[DEBUG] 推測された著者: {found_author}")
        
        result = list(set(found_authors))  # 重複除去
        print(f"[DEBUG] 最終著者リスト: {result}")
        return result
    
    def generate_smart_queries(
        self, 
        user_books: List[Dict[Any, Any]], 
        user_keywords: List[str], 
        content_type: str, 
        weight_balance: float
    ) -> List[Dict[str, str]]:
        """実用的なクエリ生成"""
        queries = []
        
        print(f"[DEBUG] スマートクエリ生成開始")
        print(f"[DEBUG] ユーザー本数: {len(user_books)}")
        print(f"[DEBUG] コンテンツタイプ: {content_type}")
        
        # 1. ユーザーキーワード
        if user_keywords:
            keyword_query = " ".join(user_keywords)
            if content_type == "manga":
                keyword_query += " 漫画"
            
            queries.append({
                "query": keyword_query,
                "type": "user_keywords"
            })
            print(f"[DEBUG] ユーザーキーワードクエリ: {keyword_query}")
        
        # 2. ジャンルベースのクエリ
        if weight_balance > 0.1:
            genres = self.extract_genres_from_titles(user_books)
            
            if genres:
                # 最も多いジャンルでクエリ作成
                main_genre = genres[0]
                genre_query = f"{main_genre} 漫画 おすすめ"
                
                queries.append({
                    "query": genre_query,
                    "type": "main_genre"
                })
                print(f"[DEBUG] ジャンルクエリ: {genre_query}")
                
                # 2番目のジャンルも追加（あれば）
                if len(genres) > 1:
                    second_genre = genres[1] 
                    second_query = f"{second_genre} 漫画 新刊"
                    
                    queries.append({
                        "query": second_query,
                        "type": "second_genre"
                    })
                    print(f"[DEBUG] 第2ジャンルクエリ: {second_query}")
        
        # 3. 著者ベースのクエリ
        if weight_balance > 0.3:
            authors = self.extract_authors_from_known_works(user_books)
            
            if authors:
                author = authors[0]
                author_query = f"{author} 他作品"
                
                queries.append({
                    "query": author_query,
                    "type": "similar_author"
                })
                print(f"[DEBUG] 著者クエリ: {author_query}")
        
        # 4. 最低限のフォールバック
        if len(queries) == 0:
            fallback = "人気 漫画" if content_type == "manga" else "人気 本"
            queries.append({
                "query": fallback,
                "type": "fallback"
            })
            print(f"[DEBUG] フォールバッククエリ: {fallback}")
        
        print(f"[DEBUG] 生成されたクエリ数: {len(queries)}")
        return queries
    
    def detect_content_type(self, user_books: List[Dict[Any, Any]]) -> str:
        """簡単なコンテンツタイプ判定"""
        return "manga"  # とりあえず漫画固定
    
    def is_similar_series(self, title: str, user_books: List[Dict[Any, Any]]) -> bool:
        """シリーズ判定"""
        title_clean = re.sub(r'[0-9巻話章編()（）\s\-\+]+', '', title.lower())
        
        if len(title_clean) < 2:
            return False
        
        for user_book in user_books:
            user_title = user_book.get('title', '')
            user_clean = re.sub(r'[0-9巻話章編()（）\s\-\+]+', '', user_title.lower())
            
            if len(user_clean) < 2:
                continue
            
            if (title_clean == user_clean or 
                (len(title_clean) > 3 and title_clean in user_clean) or
                (len(user_clean) > 3 and user_clean in title_clean)):
                return True
        
        return False
    
    # メイン関数を新しい実装に置き換え
    def generate_hybrid_queries(
        self, 
        user_books: List[Dict[Any, Any]], 
        user_keywords: List[str], 
        content_type: str, 
        weight_balance: float
    ) -> List[Dict[str, str]]:
        """新しいスマートクエリを使用"""
        return self.generate_smart_queries(user_books, user_keywords, content_type, weight_balance)

analyzer = TextAnalyzer()

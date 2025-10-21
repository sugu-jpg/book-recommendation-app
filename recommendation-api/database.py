import psycopg2
from psycopg2.extras import RealDictCursor
import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class DatabaseConnection:
    def __init__(self):
        self.connection_string = os.getenv("DATABASE_URL")
    
    def get_connection(self):
        return psycopg2.connect(self.connection_string)
    
    def get_user_books(self, user_id: str) -> List[Dict[Any, Any]]:
        """ユーザーの登録済み本を取得"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    "SELECT * FROM \"Book\" WHERE user_id = %s ORDER BY created_at DESC",
                    (user_id,)
                )
                books = []
                for row in cursor.fetchall():
                    book = dict(row)
                    # rating の型を確実に数値にする
                    if book.get('rating') is None:
                        book['rating'] = 3.0
                    else:
                        try:
                            book['rating'] = float(book['rating'])
                        except (ValueError, TypeError):
                            book['rating'] = 3.0
                    books.append(book)
                return books
    
    def get_all_books(self) -> List[Dict[Any, Any]]:
        """全ユーザーの本を取得（レコメンド分析用）"""
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("SELECT * FROM \"Book\"")
                return [dict(row) for row in cursor.fetchall()]

# グローバルインスタンス
db = DatabaseConnection()

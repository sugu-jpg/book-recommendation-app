from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any
from enum import Enum
import re

# 既存のインポート
from database import db
from text_analyzer import analyzer
from google_books import google_books

# 新しく追加
from ml_recommender import ml_recommender
import numpy as np

load_dotenv()

app = FastAPI(title="Book Recommendation API", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ContentType(str, Enum):
    AUTO = "auto"
    MANGA = "manga"
    NOVEL = "novel" 
    LIGHT_NOVEL = "light_novel"
    GENERAL = "general"

@app.get("/")
async def root():
    return {"message": "Book Recommendation API with Machine Learning"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "ml_enabled": True}

# 既存のエンドポイント...
@app.get("/api/books/{user_id}")
async def get_user_books(user_id: str):
    """ユーザーの本を取得"""
    try:
        books = db.get_user_books(user_id)
        return {"books": books}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/books")
async def get_all_books():
    """全ての本を取得"""
    try:
        books = db.get_all_books()
        return {"books": books}
    except Exception as e:
        return {"error": str(e)}

# 新しい機械学習エンドポイント
@app.get("/api/ml-recommendations/{user_id}")
async def get_ml_recommendations(
    user_id: str,
    keywords: Optional[str] = Query(None, description="検索キーワード"),
    limit: int = Query(10, description="推薦数")
):
    """機械学習ベースの推薦"""
    try:
        print(f"[API] ML推薦リクエスト開始 - ユーザー: {user_id}")
        
        # 1. ユーザーの本を取得
        print(f"[API] ステップ1: ユーザー本取得開始")
        user_books = db.get_user_books(user_id)
        print(f"[API] ステップ1完了: ユーザー本数: {len(user_books)}")
        
        if not user_books:
            return {
                "message": "ユーザーの本が見つかりません", 
                "recommendations": [],
                "debug_info": "ユーザーの本が0件"
            }
        
        # 2. 外部検索で候補を取得
        print(f"[API] ステップ2: 外部検索開始")
        search_queries = ["人気 漫画 おすすめ", "話題 コミック 新刊", "評価 高い マンガ"]
        
        if keywords:
            user_keywords = [k.strip() for k in keywords.split(',') if k.strip()]
            search_queries = [" ".join(user_keywords + ["漫画", "おすすめ"])]
        
        external_books = []
        for i, query in enumerate(search_queries):
            print(f"[API] 外部検索 {i+1}/{len(search_queries)}: {query}")
            try:
                books = google_books.search_books(query, 20)
                external_books.extend(books)
                print(f"[API] 外部検索 {i+1} 結果: {len(books)}件")
            except Exception as search_error:
                print(f"[API] 外部検索 {i+1} エラー: {search_error}")
        
        print(f"[API] ステップ2完了: 外部検索結果合計: {len(external_books)}件")
        
        if not external_books:
            return {
                "message": "外部検索結果が見つかりません", 
                "recommendations": [],
                "debug_info": "外部検索結果が0件"
            }
        
        # 3. 機械学習で推薦
        print(f"[API] ステップ3: ML推薦開始")
        try:
            ml_recommendations = ml_recommender.get_ml_recommendations(
                user_books, external_books, limit
            )
            print(f"[API] ステップ3完了: ML推薦結果: {len(ml_recommendations)}件")
        except Exception as ml_error:
            print(f"[API] ステップ3エラー: {ml_error}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"ML推薦エラー: {str(ml_error)}",
                "recommendations": [],
                "debug_info": f"ML推薦処理でエラー: {str(ml_error)}"
            }
        
        return {
            "strategy": "TF-IDF + コサイン類似度",
            "user_books_count": len(user_books),
            "external_books_count": len(external_books),
            "ml_algorithm": "TF-IDF Vectorization + Cosine Similarity",
            "ml_features": len(ml_recommender.feature_names) if hasattr(ml_recommender.feature_names, '__len__') and len(ml_recommender.feature_names) > 0 else 0,
            "recommendations": ml_recommendations,
            "debug_info": f"正常完了: ユーザー本{len(user_books)}件, 外部{len(external_books)}件, 推薦{len(ml_recommendations)}件"
        }
    
    except Exception as e:
        print(f"[API] 全体エラー: {e}")
        import traceback
        traceback.print_exc()
        return {
            "error": str(e),
            "recommendations": [],
            "debug_info": f"全体エラー: {str(e)}"
        }

@app.get("/api/ml-analysis/{user_id}")
async def get_ml_analysis(user_id: str):
    """機械学習分析の詳細情報"""
    try:
        print(f"[API] ML分析リクエスト - ユーザー: {user_id}")
        
        user_books = db.get_user_books(user_id)
        
        if not user_books:
            return {"error": "ユーザーの本が見つかりません"}
        
        # 外部本も少し取得（分析用）
        external_books = google_books.search_books("人気 漫画", 10)
        all_books = user_books + external_books
        
        # TF-IDFの詳細分析
        corpus = ml_recommender.create_book_corpus(all_books)
        ml_recommender.fit_tfidf(corpus)
        
        # ユーザープロファイル作成
        user_profile = ml_recommender.create_user_profile(user_books)
        
        # 重要な特徴語を抽出
        if len(ml_recommender.feature_names) > 0 and len(user_profile) > 0:
            top_features_indices = np.argsort(user_profile)[-10:][::-1]
            top_features = [ml_recommender.feature_names[i] for i in top_features_indices if i < len(ml_recommender.feature_names)]
            top_scores = [user_profile[i] for i in top_features_indices if i < len(user_profile)]
        else:
            top_features = []
            top_scores = []
        
        return {
            "algorithm": "TF-IDF (Term Frequency-Inverse Document Frequency)",
            "total_features": len(ml_recommender.feature_names),
            "user_profile_dimensions": len(user_profile),
            "corpus_size": len(corpus),
            "top_user_features": [
                {"feature": feat, "tfidf_score": float(score)} 
                for feat, score in zip(top_features, top_scores) if score > 0
            ],
            "user_books_analysis": [
                {
                    "title": book.get('title'),
                    "processed_text": ml_recommender.preprocess_text(book.get('title', ''), book.get('description', ''))
                }
                for book in user_books[:5]  # 最初の5冊のみ
            ],
            "ml_explanation": {
                "tfidf": "各単語の重要度を文書内頻度(TF)と逆文書頻度(IDF)で計算",
                "cosine_similarity": "ベクトル空間でのコサイン類似度による類似性測定",
                "user_profile": "ユーザーの読書履歴から好みのベクトル表現を生成",
                "recommendation_process": "1. テキスト前処理 → 2. TF-IDFベクトル化 → 3. ユーザープロファイル作成 → 4. コサイン類似度計算 → 5. 類似度順ソート"
            }
        }
    
    except Exception as e:
        print(f"[API] ML分析エラー: {e}")
        return {"error": str(e)}

# 既存のレコメンドエンドポイント（従来版）
@app.get("/api/recommendations/{user_id}")
async def get_recommendations(
    user_id: str, 
    limit: int = 10,
    keywords: Optional[str] = Query(None, description="ユーザー指定キーワード（カンマ区切り）"),
    content_type: ContentType = Query(ContentType.AUTO, description="コンテンツタイプ"),
    weight_balance: float = Query(0.5, description="自動分析とキーワードの重み比率"),
    prefer_volume_one: bool = Query(True, description="1巻を優先するか")
):
    """従来のハイブリッド推薦（非ML）"""
    try:
        user_books = db.get_user_books(user_id)
        
        if not user_books:
            return {"message": "ユーザーの本が見つかりません", "recommendations": []}
        
        # 従来のロジック...
        user_keywords = []
        if keywords:
            user_keywords = [k.strip() for k in keywords.split(',') if k.strip()]
        
        if content_type == ContentType.AUTO:
            detected_type = analyzer.detect_content_type(user_books)
        else:
            detected_type = content_type.value
        
        search_queries = analyzer.generate_hybrid_queries(
            user_books, 
            user_keywords, 
            detected_type, 
            weight_balance
        )
        
        all_recommendations = []
        query_info = []
        
        for query_data in search_queries:
            query = query_data['query']
            query_type = query_data['type']
            
            books = google_books.search_books_with_filters(
                query, 
                detected_type, 
                limit//len(search_queries) + 5
            )
            all_recommendations.extend(books)
            query_info.append({
                "query": query,
                "type": query_type,
                "found": len(books)
            })
        
        # フィルタリング
        filtered_recommendations = []
        seen_base_titles = set()
        user_base_titles = set()
        
        for user_book in user_books:
            user_title = user_book.get('title', '')
            user_base = google_books.extract_base_title(user_title).lower()
            user_base_titles.add(user_base)
        
        for book in all_recommendations:
            book_title = book['title']
            book_base = google_books.extract_base_title(book_title).lower()
            
            exact_match = any(
                book_title.lower().strip() == user_book['title'].lower().strip() 
                for user_book in user_books
            )
            
            base_already_seen = book_base in seen_base_titles
            user_has_series = book_base in user_base_titles
            
            if (not exact_match and 
                not base_already_seen and 
                not user_has_series and 
                book_title and 
                len(book_base) > 1):
                
                filtered_recommendations.append(book)
                seen_base_titles.add(book_base)
        
        return {
            "strategy": "従来のルールベース推薦",
            "content_type_setting": content_type.value,
            "actual_content_type": detected_type,
            "prefer_volume_one": prefer_volume_one,
            "user_keywords": user_keywords,
            "weight_balance": weight_balance,
            "user_books_count": len(user_books),
            "query_info": query_info,
            "total_found": len(all_recommendations),
            "recommendations": filtered_recommendations[:limit]
        }
    
    except Exception as e:
        print(f"エラー: {e}")
        return {"error": str(e)}

@app.get("/api/test-ml/{user_id}")
async def test_ml_recommendations(user_id: str):
    """ML推薦のテスト"""
    try:
        print(f"[TEST] テスト開始 - ユーザー: {user_id}")
        
        # 1. データベース接続テスト
        user_books = db.get_user_books(user_id)
        print(f"[TEST] ユーザー本数: {len(user_books)}")
        
        # 2. 外部API検索テスト
        external_books = google_books.search_books("人気 漫画", 5)
        print(f"[TEST] 外部検索結果: {len(external_books)}")
        
        # 3. ML推薦テスト（エラーハンドリング付き）
        try:
            recommendations = ml_recommender.get_ml_recommendations(
                user_books, external_books, 3
            )
            print(f"[TEST] ML推薦結果: {len(recommendations)}")
        except Exception as ml_error:
            print(f"[TEST] ML推薦エラー: {ml_error}")
            return {
                "status": "ml_error",
                "error": str(ml_error),
                "user_books_count": len(user_books),
                "external_books_count": len(external_books)
            }
        
        return {
            "status": "success",
            "user_books_count": len(user_books),
            "external_books_count": len(external_books),
            "recommendations_count": len(recommendations),
            "sample_user_books": [book.get('title') for book in user_books[:3]],
            "sample_external_books": [book.get('title') for book in external_books[:3]]
        }
        
    except Exception as e:
        print(f"[TEST] テスト全体エラー: {e}")
        return {"status": "error", "error": str(e)}

@app.get("/api/debug-recommendations/{user_id}")
async def debug_recommendations(user_id: str):
    """推薦結果をデバッグ"""
    try:
        user_books = db.get_user_books(user_id)
        external_books = google_books.search_books("人気 漫画", 10)
        
        # コーパス作成
        all_books = user_books + external_books
        corpus = ml_recommender.create_book_corpus(all_books)
        ml_recommender.fit_tfidf(corpus)
        
        # ユーザープロファイル作成
        user_profile = ml_recommender.create_user_profile(user_books)
        
        # 類似度計算
        similarity_scores = ml_recommender.calculate_similarity_scores(user_profile)
        
        # スコア0の本を調べる
        zero_score_books = []
        high_score_books = []
        
        for book_index, score in similarity_scores:
            if book_index >= len(user_books):  # 外部本のみ
                book_info = {
                    "title": ml_recommender.book_data[book_index]['title'],
                    "processed_text": ml_recommender.book_data[book_index]['processed_text'],
                    "similarity_score": float(score),
                    "text_length": len(ml_recommender.book_data[book_index]['processed_text'])
                }
                
                if score == 0.0:
                    zero_score_books.append(book_info)
                elif score > 0.05:
                    high_score_books.append(book_info)
        
        # ユーザープロファイルの重要特徴語を取得
        top_features_indices = user_profile.argsort()[-10:][::-1]
        top_user_features = [
            {
                "feature": ml_recommender.feature_names[i],
                "score": float(user_profile[i])
            } 
            for i in top_features_indices if user_profile[i] > 0
        ]
        
        return {
            "user_top_features": top_user_features,
            "zero_score_books": zero_score_books[:5],
            "high_score_books": high_score_books[:5],
            "total_zero_books": len(zero_score_books),
            "total_high_books": len(high_score_books)
        }
        
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

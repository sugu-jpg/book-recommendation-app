from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import re

# 既存のインポート
from database import db
from text_analyzer import analyzer
from google_books import google_books

# 新しく追加
from ml_recommender import ml_recommender
import numpy as np
import random
from collections import defaultdict

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
    limit: int = Query(10, description="推薦数"),
    diversity: float = Query(0.3, description="多様性係数(0-1)"),
    randomness: float = Query(0.2, description="ランダム性係数(0-1)"),
    use_title_in_tfidf: bool = Query(False, description="TF-IDFでタイトルを使用するか"),
    filter_same_series: bool = Query(True, description="同じシリーズを除外するか")
):
    """改善された機械学習推薦"""
    try:
        print(f"[API] ML推薦リクエスト開始")
        
        user_books = db.get_user_books(user_id)
        print(f"[API] ユーザー本数: {len(user_books)}")
        
        if not user_books:
            return {"message": "ユーザーの本が見つかりません", "recommendations": []}

        # 外部検索を強制実行
        print(f"[API] 外部検索を強制実行")
        external_books = []
        
        # ユーザーの好みを検出
        user_preferences = detect_user_preferences(user_books)
        print(f"[API] ユーザー好み検出: {user_preferences}")

        # ユーザー個人化された検索クエリを生成
        search_queries = generate_personalized_queries(user_books)
        print(f"[API] 個人化検索クエリ: {search_queries}")

        # 複数の検索を実行（検索数を増やす）
        for i, query in enumerate(search_queries):
            try:
                print(f"[API] 検索 {i+1}/{len(search_queries)}: {query}")
                books = google_books.search_books(query, 25)  # 15→25に増加
                print(f"[API] 結果: {len(books)}件")
                external_books.extend(books)
            except Exception as e:
                print(f"[API] 検索エラー: {e}")
                continue

        # 追加の汎用検索を実行（フォールバック）
        additional_queries = [
            "人気 漫画 おすすめ",
            "話題 コミック 新刊",
            "ランキング 漫画",
            "評価 高い 漫画",
            "新作 漫画"
        ]

        for query in additional_queries:
            try:
                print(f"[API] 追加検索: {query}")
                books = google_books.search_books(query, 20)
                print(f"[API] 追加結果: {len(books)}件")
                external_books.extend(books)
            except Exception as e:
                print(f"[API] 追加検索エラー: {e}")
                continue

        # 重複除去
        unique_external_books = []
        seen_titles = set()
        for book in external_books:
            title = book.get('title', '')
            if title and title not in seen_titles:
                unique_external_books.append(book)
                seen_titles.add(title)

        print(f"[API] 重複除去後: {len(unique_external_books)}件")

        # ユーザーの好みに基づくフィルタリング
        unique_external_books = filter_by_user_preferences_relaxed(unique_external_books, user_preferences)
        print(f"[API] 個人化フィルタリング後: {len(unique_external_books)}件")
        
        # 外部本が0の場合の応急処置
        if len(unique_external_books) == 0:
            print(f"[API] 応急処置: ダミー本を追加")
            unique_external_books = [
                {
                    "title": "進撃の巨人 外伝",
                    "authors": ["諫山創"],
                    "description": "巨人との戦いを描いた名作",
                    "image": "",
                    "google_id": "dummy1",
                    "rating": 4.5,
                    "categories": ["Comics & Graphic Novels"]
                },
                {
                    "title": "呪術廻戦 公式ファンブック",
                    "authors": ["芥見下々"],
                    "description": "呪術師の戦いを描く",
                    "image": "",
                    "google_id": "dummy2",
                    "rating": 4.3,
                    "categories": ["Comics & Graphic Novels"]
                },
                {
                    "title": "鬼滅の刃 外伝",
                    "authors": ["吾峠呼世晴"],
                    "description": "鬼との戦いを描いた作品",
                    "image": "",
                    "google_id": "dummy3",
                    "rating": 4.4,
                    "categories": ["Comics & Graphic Novels"]
                }
            ]
        
        # ML推薦を実行
        print(f"[API] ML推薦実行: ユーザー本={len(user_books)}, 外部本={len(unique_external_books)}")
        
        ml_recommendations = ml_recommender.get_ml_recommendations(
            user_books, 
            unique_external_books, 
            limit, 
            diversity, 
            randomness,
            use_title_in_tfidf,
            filter_same_series
        )
        
        print(f"[API] ML推薦結果: {len(ml_recommendations)}件")
        
        # 推薦数が不足している場合のフォールバック
        if len(ml_recommendations) < limit:
            print(f"[API] 推薦数不足 ({len(ml_recommendations)}/{limit}) - フォールバック実行")
            
            # より緩い条件でML推薦を再実行
            fallback_recommendations = ml_recommender.get_ml_recommendations(
                user_books, 
                unique_external_books, 
                limit * 2,  # より多く取得
                diversity * 0.5,  # 多様性を下げる
                randomness * 0.5,  # ランダム性を下げる
                use_title_in_tfidf,
                False  # シリーズフィルタリングを無効化
            )
            
            # 重複除去して結合
            existing_titles = {rec.get('title', '') for rec in ml_recommendations}
            for rec in fallback_recommendations:
                if rec.get('title', '') not in existing_titles and len(ml_recommendations) < limit:
                    ml_recommendations.append(rec)
                    existing_titles.add(rec.get('title', ''))
            
            print(f"[API] フォールバック後: {len(ml_recommendations)}件")
        
        # 特徴語数の取得（エラー回避）
        ml_features = 0
        try:
            if hasattr(ml_recommender, 'feature_names') and ml_recommender.feature_names:
                ml_features = len(ml_recommender.feature_names)
        except:
            ml_features = 0
        
        return {
            "recommendations": ml_recommendations,
            "total_count": len(ml_recommendations),
            "algorithm": "TF-IDF + Cosine Similarity",
            "ml_features": ml_features,
            "parameters": {
                "diversity": diversity,
                "randomness": randomness,
                "use_title_in_tfidf": use_title_in_tfidf,
                "filter_same_series": filter_same_series
            }
        }
        
    except Exception as e:
        print(f"[API] ML推薦エラー: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e), "recommendations": []}

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
        
        # TF-IDFの詳細分析（use_title=Trueで分析）
        corpus = ml_recommender.create_book_corpus(all_books, use_title=True)
        ml_recommender.fit_tfidf(corpus)
        
        # ユーザープロファイル作成
        user_profile = ml_recommender.create_user_profile(user_books)
        
        # 安全な特徴語抽出
        top_user_features = []
        try:
            if (len(ml_recommender.feature_names) > 0 and 
                user_profile is not None and 
                user_profile.size > 0):
                
                top_features_indices = np.argsort(user_profile)[-10:][::-1]
                top_features = [ml_recommender.feature_names[i] for i in top_features_indices if i < len(ml_recommender.feature_names)]
                top_scores = [float(user_profile[i]) for i in top_features_indices if i < user_profile.size]
                
                top_user_features = [
                    {"feature": feat, "tfidf_score": score} 
                    for feat, score in zip(top_features, top_scores) if score > 0
                ]
        except Exception as feature_error:
            print(f"[API] 特徴語抽出エラー: {feature_error}")
            top_user_features = []
        
        # 安全なユーザー本分析
        user_books_analysis = []
        try:
            user_books_analysis = [
                {
                    "title": book.get('title'),
                    "processed_text": ml_recommender.preprocess_text(book.get('title', ''), book.get('description', ''), use_title=True)
                }
                for book in user_books[:5]  # 最初の5冊のみ
            ]
        except Exception as analysis_error:
            print(f"[API] ユーザー本分析エラー: {analysis_error}")
            user_books_analysis = []
        
        return {
            "algorithm": "TF-IDF (Term Frequency-Inverse Document Frequency)",
            "total_features": len(ml_recommender.feature_names) if ml_recommender.feature_names else 0,
            "user_profile_dimensions": int(user_profile.size) if user_profile is not None else 0,
            "corpus_size": len(corpus),
            "top_user_features": top_user_features,
            "user_books_analysis": user_books_analysis,
            "ml_explanation": {
                "tfidf": "各単語の重要度を文書内頻度(TF)と逆文書頻度(IDF)で計算",
                "cosine_similarity": "ベクトル空間でのコサイン類似度による類似性測定",
                "user_profile": "ユーザーの読書履歴から好みのベクトル表現を生成",
                "recommendation_process": "1. テキスト前処理 → 2. TF-IDFベクトル化 → 3. ユーザープロファイル作成 → 4. コサイン類似度計算 → 5. 類似度順ソート"
            }
        }
    
    except Exception as e:
        print(f"[API] ML分析エラー: {e}")
        import traceback
        traceback.print_exc()
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
        corpus = ml_recommender.create_book_corpus(all_books, use_title=True)  # use_titleパラメータを追加
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
        
        # ユーザープロファイルの重要特徴語を取得（修正）
        if user_profile.size > 0:
            top_features_indices = user_profile.argsort()[-10:][::-1]
            top_user_features = [
                {
                    "feature": ml_recommender.feature_names[i],
                    "score": float(user_profile[i])
                } 
                for i in top_features_indices 
                if i < len(ml_recommender.feature_names) and float(user_profile[i]) > 0  # 修正！
            ]
        else:
            top_user_features = []
        
        return {
            "user_top_features": top_user_features,
            "zero_score_books": zero_score_books[:5],
            "high_score_books": high_score_books[:5],
            "total_zero_books": len(zero_score_books),
            "total_high_books": len(high_score_books)
        }
        
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/corpus-debug/{user_id}")
async def corpus_debug(user_id: str):
    """コーパスの詳細デバッグ"""
    try:
        user_books = db.get_user_books(user_id)
        external_books = google_books.search_books("人気 漫画", 10)
        
        print(f"[DEBUG] ユーザー本数: {len(user_books)}")
        print(f"[DEBUG] 外部本数: {len(external_books)}")
        
        # コーパス作成の詳細を確認
        all_books = user_books + external_books
        
        # 各本の詳細を確認
        book_details = []
        for i, book in enumerate(all_books):
            title = book.get('title', '') or ''
            description = book.get('description', '') or ''
            
            # 前処理前後のテキストを確認
            processed_title = ml_recommender.preprocess_text(title, description, use_title=True)
            processed_desc_only = ml_recommender.preprocess_text(title, description, use_title=False)
            
            book_detail = {
                "index": i,
                "title": title,
                "description": description[:100] + "..." if len(description) > 100 else description,
                "description_length": len(description),
                "processed_with_title": processed_title,
                "processed_desc_only": processed_desc_only,
                "is_user_book": i < len(user_books)
            }
            book_details.append(book_detail)
        
        # タイトルありでコーパス作成
        corpus_with_title = ml_recommender.create_book_corpus(all_books, use_title=True)
        valid_corpus_with_title = [text for text in corpus_with_title if text and text.strip()]
        
        # タイトルなしでコーパス作成
        corpus_without_title = ml_recommender.create_book_corpus(all_books, use_title=False)
        valid_corpus_without_title = [text for text in corpus_without_title if text and text.strip()]
        
        return {
            "user_books_count": len(user_books),
            "external_books_count": len(external_books),
            "total_books": len(all_books),
            "corpus_with_title": {
                "total": len(corpus_with_title),
                "valid": len(valid_corpus_with_title),
                "samples": valid_corpus_with_title[:5]
            },
            "corpus_without_title": {
                "total": len(corpus_without_title),
                "valid": len(valid_corpus_without_title),
                "samples": valid_corpus_without_title[:5]
            },
            "book_details": book_details[:10],  # 最初の10冊のみ
            "tfidf_will_work_with_title": len(valid_corpus_with_title) >= 2,
            "tfidf_will_work_without_title": len(valid_corpus_without_title) >= 2
        }
        
    except Exception as e:
        print(f"[DEBUG] エラー: {e}")
        return {"error": str(e)}

# 新しいテストエンドポイントを追加
@app.get("/api/test-google-books")
async def test_google_books_api():
    """Google Books APIのテスト"""
    try:
        print("[TEST] Google Books APIテスト開始")
        
        # 直接APIを呼び出してテスト
        test_query = "人気 漫画"
        books = google_books.search_books(test_query, 5)
        
        print(f"[TEST] 検索結果: {len(books)}件")
        
        result = {
            "query": test_query,
            "result_count": len(books),
            "books": books[:3] if books else []
        }
        
        return result
        
    except Exception as e:
        print(f"[TEST] Google Books APIエラー: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def generate_personalized_queries(user_books):
    """ユーザーの読書履歴に基づいた個人化検索クエリ"""
    queries = []
    user_titles = [book.get('title', '') for book in user_books]
    
    # ユーザーの実際の読書履歴から著者を抽出
    user_authors = set()
    for book in user_books:
        authors = book.get('authors', []) or []
        user_authors.update(authors)
    
    # 著者ベースの検索（個人化）
    for author in list(user_authors)[:3]:  # 最大3人の著者
        if author:
            queries.append(f"{author} 他の作品 漫画")
    
    # ユーザーのタイトルから具体的なキーワードを抽出
    title_keywords = set()
    for title in user_titles:
        # タイトルから意味のある単語を抽出
        words = title.split()
        for word in words:
            if len(word) > 2 and word not in ['の', 'は', 'が', 'を', 'に', 'で', 'と']:
                title_keywords.add(word)
    
    # ユーザー固有のキーワードベース検索
    for keyword in list(title_keywords)[:3]:  # 最大3つのキーワード
        queries.append(f"{keyword} 類似 漫画")
    
    # フォールバック：汎用的だが偏りのない検索
    if not queries:
        queries = ['人気 漫画', '新刊 コミック', '話題 漫画']
    
    return queries[:5]

def detect_user_preferences(user_books):
    """ユーザーの好みを検出"""
    preferences = {
        'likes_jump': 0,
        'likes_narou': 0,
        'likes_sports': 0,
        'likes_romance': 0,
        'likes_seinen': 0
    }
    
    for book in user_books:
        title = book.get('title', '')
        description = book.get('description', '')
        
        # ジャンプ系の検出
        if any(keyword in title.lower() for keyword in ['ワンピース', 'ナルト', '呪術', '進撃', 'ヒーロー', 'ドラゴンボール']):
            preferences['likes_jump'] += 1
        
        # なろう系の検出
        if any(keyword in title or keyword in description for keyword in ['異世界', '転生', '魔王', '勇者', 'チート']):
            preferences['likes_narou'] += 1
        
        # スポーツ系の検出
        if any(keyword in title for keyword in ['ハイキュー', 'スラムダンク', 'バスケ', 'サッカー', 'テニス']):
            preferences['likes_sports'] += 1
        
        # 恋愛系の検出
        if any(keyword in title for keyword in ['恋', 'ラブ', '花', '着せ替え']):
            preferences['likes_romance'] += 1
    
    return preferences

def filter_by_user_preferences_relaxed(books, user_preferences):
    """ユーザーの好みに基づく緩和されたフィルタリング"""
    filtered = []
    
    for book in books:
        title = book.get('title', '')
        description = book.get('description', '')
        
        # 極端になろう系のみ除外（ユーザーがなろう系を全く読んでいない場合）
        if user_preferences['likes_narou'] == 0:
            extreme_narou_keywords = ['異世界転生', 'チート能力', '魔王討伐', '勇者召喚']
            if any(keyword in title for keyword in extreme_narou_keywords):
                print(f"[API] 極端ななろう系除外: {title}")
                continue
        
        # その他は優先度調整のみ（除外しない）
        preference_score = 1.0
        
        # ユーザーがジャンプ系を好む場合、ジャンプ系に重み付け
        if user_preferences['likes_jump'] > 0:
            jump_keywords = ['バトル', 'アクション', '友情', '成長']
            if any(keyword in title or keyword in description for keyword in jump_keywords):
                preference_score *= 1.2
        
        # ユーザーがスポーツ系を好む場合、スポーツ系に重み付け
        if user_preferences['likes_sports'] > 0:
            sports_keywords = ['スポーツ', '部活', '青春', '大会']
            if any(keyword in title or keyword in description for keyword in sports_keywords):
                preference_score *= 1.3
        
        book['preference_score'] = preference_score
        filtered.append(book)
    
    return filtered

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

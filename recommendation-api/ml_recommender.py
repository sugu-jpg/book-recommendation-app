# recommendation-api/ml_recommender.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from typing import List, Dict, Any, Tuple
import re

class MLBookRecommender:
    def __init__(self):
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,
            ngram_range=(1, 2),
            min_df=1,
            max_df=0.8
        )
        self.book_vectors = None
        self.book_data = []
        self.feature_names = []
        
    def preprocess_text(self, title: str, description: str = "") -> str:
        """テキストの前処理"""
        print(f"[ML] 前処理開始: {title[:30]}...")
        
        # None値のチェック
        if title is None:
            title = ""
        if description is None:
            description = ""
        
        # タイトルと説明を結合
        combined_text = f"{title} {description}"
        
        # 巻数除去
        cleaned = re.sub(r'[0-9]+巻|第[0-9]+巻|vol\.?\s*[0-9]+|[0-9]+$', '', combined_text)
        # 特殊版の表記除去
        cleaned = re.sub(r'モノクロ版|カラー版|完全版|新装版', '', cleaned)
        # 特殊文字除去
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        # 余分な空白除去
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        result = cleaned.lower()
        print(f"[ML] 前処理結果: {result}")
        return result
    
    def create_book_corpus(self, all_books: List[Dict[Any, Any]]) -> List[str]:
        """全ての本からコーパスを作成"""
        print(f"[ML] コーパス作成開始 - 対象本数: {len(all_books)}")
        
        corpus = []
        self.book_data = []
        
        for i, book in enumerate(all_books):
            title = book.get('title', '') or ''
            description = book.get('description', '') or ''
            
            # テキスト前処理
            processed_text = self.preprocess_text(title, description)
            corpus.append(processed_text)
            
            # 本のメタデータを保存
            book_metadata = {
                'title': title,
                'description': description,
                'processed_text': processed_text,
                'google_id': book.get('google_id', ''),
                'authors': book.get('authors', []) or [],
                'image': book.get('image', '') or '',
                'rating': book.get('rating', 0) or 0,
                'original_index': i
            }
            self.book_data.append(book_metadata)
        
        print(f"[ML] コーパス作成完了 - コーパスサイズ: {len(corpus)}")
        return corpus
    
    def fit_tfidf(self, corpus: List[str]):
        """TF-IDFモデルの学習"""
        print(f"[ML] TF-IDF学習開始 - コーパスサイズ: {len(corpus)}")
        
        try:
            # 空のテキストを除外
            valid_corpus = [text for text in corpus if text and text.strip()]
            
            if len(valid_corpus) < 2:
                print(f"[ML] 警告: コーパスが小さすぎます ({len(valid_corpus)})")
                # 最小限のTF-IDFモデルを作成
                self.book_vectors = np.zeros((len(corpus), 10))
                self.feature_names = ['dummy'] * 10
                return
            
            # TF-IDFベクトル化
            self.book_vectors = self.tfidf_vectorizer.fit_transform(valid_corpus)
            self.feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            print(f"[ML] TF-IDFベクトル形状: {self.book_vectors.shape}")
            print(f"[ML] 抽出された特徴語数: {len(self.feature_names)}")
            
        except Exception as e:
            print(f"[ML] TF-IDF学習エラー: {e}")
            # フォールバック
            self.book_vectors = np.zeros((len(corpus), 10))
            self.feature_names = ['dummy'] * 10
    
    def create_user_profile(self, user_books: List[Dict[Any, Any]]) -> np.ndarray:
        """ユーザープロファイルを作成"""
        print(f"[ML] ユーザープロファイル作成開始 - ユーザー本数: {len(user_books)}")
        
        # 空チェック
        if not user_books:
            print(f"[ML] ユーザー本が空です")
            return np.zeros(10)
        
        if self.book_vectors is None:
            print(f"[ML] book_vectorsが初期化されていません")
            return np.zeros(10)
        
        try:
            # ユーザーの本を特定
            user_indices = []
            for user_book in user_books:
                user_title = (user_book.get('title') or '').lower()
                if not user_title:
                    continue
                    
                for i, book_data in enumerate(self.book_data):
                    book_title = (book_data.get('title') or '').lower()
                    if book_title == user_title:
                        user_indices.append(i)
                        break
            
            print(f"[ML] 見つかったユーザー本のインデックス: {user_indices}")
            
            # user_indices が空の場合
            if not user_indices:
                print(f"[ML] ユーザー本が見つからないため、空のプロファイルを作成")
                return np.zeros(self.book_vectors.shape[1])
            
            # 評価による重み付け
            weights = []
            valid_vectors = []
            
            for i, idx in enumerate(user_indices):
                # 評価値の処理
                rating = 3.0  # デフォルト値
                if i < len(user_books):
                    user_rating = user_books[i].get('rating')
                    if user_rating is not None:
                        try:
                            rating = float(user_rating)
                            if rating <= 0:
                                rating = 3.0
                        except (ValueError, TypeError):
                            rating = 3.0
                
                weight = rating / 5.0
                weights.append(weight)
                
                # ベクトルの取得
                if idx < self.book_vectors.shape[0]:
                    if hasattr(self.book_vectors[idx], 'toarray'):
                        valid_vectors.append(self.book_vectors[idx].toarray().flatten())
                    else:
                        valid_vectors.append(self.book_vectors[idx].flatten())
            
            # valid_vectors が空の場合
            if not valid_vectors:
                print(f"[ML] 有効なベクトルが見つからない")
                return np.zeros(self.book_vectors.shape[1])
            
            # 重み付き平均でユーザープロファイルを作成
            weighted_sum = np.zeros(len(valid_vectors[0]))
            total_weight = 0
            
            for vector, weight in zip(valid_vectors, weights):
                weighted_sum += vector * weight
                total_weight += weight
            
            if total_weight > 0:
                user_profile = weighted_sum / total_weight
            else:
                user_profile = np.mean(valid_vectors, axis=0)
            
            print(f"[ML] ユーザープロファイル作成完了 - 次元数: {len(user_profile)}")
            return user_profile
            
        except Exception as e:
            print(f"[ML] ユーザープロファイル作成エラー: {e}")
            import traceback
            traceback.print_exc()
            return np.zeros(self.book_vectors.shape[1] if self.book_vectors is not None else 10)
    
    def calculate_similarity_scores(self, user_profile: np.ndarray) -> List[Tuple[int, float]]:
        """コサイン類似度による類似度計算"""
        print(f"[ML] 類似度計算開始")
        
        if self.book_vectors is None:
            print(f"[ML] book_vectorsがNullです")
            return []
        
        # user_profile の形状チェック
        if user_profile.size == 0:
            print(f"[ML] ユーザープロファイルが空です")
            return []
        
        try:
            # ユーザープロファイルと全ての本の類似度を計算
            user_profile_reshaped = user_profile.reshape(1, -1)
            
            # book_vectorsがスパース行列の場合の処理
            if hasattr(self.book_vectors, 'toarray'):
                book_vectors_dense = self.book_vectors.toarray()
            else:
                book_vectors_dense = self.book_vectors
            
            similarity_scores = cosine_similarity(user_profile_reshaped, book_vectors_dense)
            
            # (インデックス, 類似度スコア)のリストを作成
            scores_with_index = [(i, float(score)) for i, score in enumerate(similarity_scores[0])]
            
            # 類似度スコア順にソート
            scores_with_index.sort(key=lambda x: x[1], reverse=True)
            
            if scores_with_index:
                print(f"[ML] 類似度計算完了 - 最高スコア: {scores_with_index[0][1]:.4f}")
                print(f"[ML] 平均スコア: {np.mean([score for _, score in scores_with_index]):.4f}")
            
            return scores_with_index
            
        except Exception as e:
            print(f"[ML] 類似度計算エラー: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_ml_recommendations(
        self, 
        user_books: List[Dict[Any, Any]], 
        external_books: List[Dict[Any, Any]], 
        num_recommendations: int = 10
    ) -> List[Dict[Any, Any]]:
        """機械学習ベースの推薦 - 完全デバッグ版"""
        print(f"[ML] ML推薦開始")
        print(f"[ML] ユーザー本数: {len(user_books)}, 外部本数: {len(external_books)}")
        
        try:
            # 1. 全ての本（ユーザーの本 + 外部検索結果）でコーパス作成
            print(f"[ML] ステップ1: コーパス作成開始")
            all_books = user_books + external_books
            corpus = self.create_book_corpus(all_books)
            print(f"[ML] ステップ1完了: コーパスサイズ {len(corpus)}")
            
            # 2. TF-IDFモデル学習
            print(f"[ML] ステップ2: TF-IDF学習開始")
            self.fit_tfidf(corpus)
            print(f"[ML] ステップ2完了: 特徴語数 {len(self.feature_names)}")
            
            # 3. ユーザープロファイル作成
            print(f"[ML] ステップ3: ユーザープロファイル作成開始")
            user_profile = self.create_user_profile(user_books)
            print(f"[ML] ステップ3完了: プロファイルサイズ {user_profile.size}")
            
            # user_profileが空の場合の明示的チェック
            if user_profile.size == 0:
                print(f"[ML] ユーザープロファイルが空のため推薦を中止")
                return []
            
            # 4. 類似度計算
            print(f"[ML] ステップ4: 類似度計算開始")
            similarity_scores = self.calculate_similarity_scores(user_profile)
            print(f"[ML] ステップ4完了: 類似度スコア数 {len(similarity_scores)}")
            
            # similarity_scoresが空の場合の明示的チェック
            if len(similarity_scores) == 0:
                print(f"[ML] 類似度スコアが空のため推薦を中止")
                return []
            
            # 5. 推薦生成
            print(f"[ML] ステップ5: 推薦生成開始")
            recommendations = []
            user_books_count = len(user_books)
            
            # ユーザーの本のタイトルを正規化して保存
            user_titles_normalized = set()
            for book in user_books:
                title = book.get('title')
                if title and isinstance(title, str):
                    normalized = re.sub(r'[0-9]+巻|第[0-9]+巻|モノクロ版|カラー版', '', title.lower()).strip()
                    if len(normalized) > 0:
                        user_titles_normalized.add(normalized)
            
            print(f"[ML] 除外対象タイトル数: {len(user_titles_normalized)}")
            
            processed_count = 0
            for book_index, similarity_score in similarity_scores:
                processed_count += 1
                
                if len(recommendations) >= num_recommendations:
                    break
                
                # 外部検索結果のみを推薦対象とする
                if book_index < user_books_count:
                    continue
                
                if book_index >= len(self.book_data):
                    continue
                
                book = self.book_data[book_index]
                book_title = book.get('title')
                
                if not book_title or not isinstance(book_title, str):
                    continue
                
                # 正規化して除外判定
                normalized_title = re.sub(r'[0-9]+巻|第[0-9]+巻|モノクロ版|カラー版', '', book_title.lower()).strip()
                
                # 除外判定
                if len(normalized_title) > 0 and normalized_title not in user_titles_normalized:
                    # ML情報を追加
                    book_with_ml = {
                        'title': book.get('title', ''),
                        'authors': book.get('authors', []),
                        'description': book.get('description', ''),
                        'image': book.get('image', ''),
                        'rating': book.get('rating', 0),
                        'google_id': book.get('google_id', ''),
                        'ml_similarity_score': float(similarity_score),
                        'recommendation_reason': f"ML類似度: {similarity_score:.3f}",
                        'algorithm': 'TF-IDF + Cosine Similarity'
                    }
                    
                    recommendations.append(book_with_ml)
                    print(f"[ML] 推薦追加 {len(recommendations)}/{num_recommendations}: {book.get('title', 'No Title')} (類似度: {similarity_score:.3f})")
            
            print(f"[ML] ステップ5完了: 処理した本数 {processed_count}, 推薦数 {len(recommendations)}")
            print(f"[ML] ML推薦完了 - {len(recommendations)}件")
            return recommendations
            
        except Exception as e:
            print(f"[ML] ML推薦エラー: {e}")
            import traceback
            traceback.print_exc()
            return []

# グローバルインスタンス
ml_recommender = MLBookRecommender()

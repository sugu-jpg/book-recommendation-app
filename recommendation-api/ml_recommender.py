# recommendation-api/ml_recommender.py
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from typing import List, Dict, Any, Tuple
import re
import random
from collections import defaultdict

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
        num_recommendations: int = 10,
        diversity_factor: float = 0.3,
        randomness: float = 0.2
    ) -> List[Dict[Any, Any]]:
        """詳細デバッグ版推薦"""
        print(f"[ML] 推薦開始")
        print(f"[ML] ユーザー本数: {len(user_books)}")
        print(f"[ML] 外部本数: {len(external_books)}")
        print(f"[ML] 合計本数: {len(user_books) + len(external_books)}")
        
        try:
            # 1-4. 従来の処理
            all_books = user_books + external_books
            print(f"[ML] all_books作成後: {len(all_books)}冊")
            
            corpus = self.create_book_corpus(all_books)
            self.fit_tfidf(corpus)
            user_profile = self.create_user_profile(user_books)
            
            if user_profile.size == 0:
                return []
                
            similarity_scores = self.calculate_similarity_scores(user_profile)
            
            if not similarity_scores:
                return []
            
            # 重要: ユーザー本数を明示的に記録
            user_books_count = len(user_books)
            print(f"[ML] ユーザー本のインデックス範囲: 0-{user_books_count-1}")
            print(f"[ML] 外部本のインデックス範囲: {user_books_count}-{len(all_books)-1}")
            
            # 上位類似度の詳細を表示
            print(f"[ML] 類似度上位10件の詳細:")
            for i, (book_index, similarity_score) in enumerate(similarity_scores[:10]):
                book_type = "ユーザー本" if book_index < user_books_count else "外部本"
                book_title = self.book_data[book_index].get('title', 'タイトルなし')
                print(f"[ML]   {i}: index={book_index}, score={similarity_score:.4f}, type={book_type}, title='{book_title[:30]}...'")
            
            # 外部本の類似度をチェック
            external_candidates = [(idx, score) for idx, score in similarity_scores if idx >= user_books_count]
            print(f"[ML] 外部本の候補数: {len(external_candidates)}")
            
            if external_candidates:
                print(f"[ML] 外部本の上位5件:")
                for i, (book_index, similarity_score) in enumerate(external_candidates[:5]):
                    book_title = self.book_data[book_index].get('title', 'タイトルなし')
                    print(f"[ML]   外部{i}: index={book_index}, score={similarity_score:.4f}, title='{book_title[:30]}...'")
            
            # 5. 外部本のみで推薦候補を作成
            all_candidates = []
            
            for book_index, similarity_score in external_candidates:
                if book_index >= len(self.book_data):
                    continue
                    
                book = self.book_data[book_index]
                book_title = book.get('title') or ''
                
                if not book_title:
                    continue
                    
                # 重複チェック（簡略化）
                user_titles = [ub.get('title', '').lower() for ub in user_books]
                if book_title.lower() in user_titles:
                    continue
                
                # 有効な候補として追加
                category = self.estimate_category(book)
                
                candidate = {
                    'book_data': book,
                    'similarity_score': float(similarity_score),
                    'category': category,
                    'title': book_title
                }
                all_candidates.append(candidate)
            
            print(f"[ML] 最終的な有効候補数: {len(all_candidates)}")
            
            # 推薦候補が少ない場合の対処
            if len(all_candidates) == 0:
                print(f"[ML] 外部本候補が0件 - 外部検索を増やす必要があります")
                return []
            
            if len(all_candidates) < num_recommendations:
                print(f"[ML] 候補不足: {len(all_candidates)}件 < {num_recommendations}件")
                return [self.format_recommendation(candidate) for candidate in all_candidates]
            
            # 7. 推薦生成
            recommendations = all_candidates[:num_recommendations]  # 簡略化
            final_recommendations = [self.format_recommendation(candidate) for candidate in recommendations]
            
            print(f"[ML] 最終推薦数: {len(final_recommendations)}")
            return final_recommendations
            
        except Exception as e:
            print(f"[ML] 推薦エラー: {e}")
            import traceback
            traceback.print_exc()
            return []

    def emergency_fallback_recommendations(self, similarity_scores: List[Tuple[int, float]], user_books_count: int) -> List[Dict[Any, Any]]:
        """緊急時のフォールバック推薦"""
        print(f"[ML] 緊急フォールバック開始")
        
        fallback_recommendations = []
        
        for book_index, similarity_score in similarity_scores:
            if book_index < user_books_count:
                continue
                
            if book_index >= len(self.book_data):
                continue
                
            book = self.book_data[book_index]
            book_title = book.get('title') or ''
            
            if book_title:
                # 最低限の推薦情報を作成
                recommendation = {
                    'title': book_title,
                    'authors': book.get('authors', []),
                    'description': book.get('description', ''),
                    'image': book.get('image', ''),
                    'rating': book.get('rating', 0),
                    'google_id': book.get('google_id', ''),
                    'ml_similarity_score': float(similarity_score),
                    'category': '未分類',
                    'recommendation_reason': f"フォールバック推薦 (類似度: {similarity_score:.3f})",
                    'algorithm': 'Emergency Fallback'
                }
                fallback_recommendations.append(recommendation)
                
                if len(fallback_recommendations) >= 12:
                    break
        
        print(f"[ML] フォールバック推薦数: {len(fallback_recommendations)}")
        return fallback_recommendations

    def estimate_category(self, book: Dict[Any, Any]) -> str:
        """本のカテゴリを推定"""
        title = (book.get('title') or '').lower()
        description = (book.get('description') or '').lower()
        text = f"{title} {description}"
        
        # カテゴリキーワード
        categories = {
            'スポーツ': ['バレー', 'サッカー', 'バスケ', 'テニス', 'スポーツ', 'ハイキュー', 'スラム'],
            'バトル': ['戦い', 'バトル', '戦闘', '格闘', '呪術', '進撃', 'ワンパン'],
            '恋愛': ['恋', '愛', 'ラブ', 'ロマンス', '結婚', 'カップル'],
            'ファンタジー': ['魔法', '異世界', 'ファンタジー', '転生', '魔物', '勇者'],
            'コメディ': ['コメディ', '笑い', 'ギャグ', 'おもしろ', 'ユーモア'],
            'ミステリー': ['謎', '推理', '事件', '犯罪', '探偵', 'ミステリー'],
            'ホラー': ['恐怖', 'ホラー', '怖い', '悪魔', 'ゾンビ', '殺人'],
            '日常': ['日常', '学校', '青春', '友情', '生活', '日々']
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return 'その他'

    def generate_flexible_recommendations(
        self, 
        candidates: List[Dict], 
        num_recommendations: int, 
        diversity_factor: float, 
        randomness: float
    ) -> List[Dict[Any, Any]]:
        """柔軟な推薦生成（推薦数を確保）"""
        
        if not candidates:
            return []
        
        # 1. 候補をスコア順にソート
        candidates_sorted = sorted(candidates, key=lambda x: x['similarity_score'], reverse=True)
        
        # 2. 多様性を考慮する場合
        if diversity_factor > 0:
            try:
                diverse_recommendations = self.apply_diversity_selection(
                    candidates_sorted, num_recommendations, diversity_factor, randomness
                )
                
                # 多様性選択で十分な数が得られた場合
                if len(diverse_recommendations) >= num_recommendations:
                    return diverse_recommendations[:num_recommendations]
                
            except Exception as e:
                print(f"[ML] 多様性選択エラー: {e}")
        
        # 3. フォールバック: 高スコア順 + 軽いランダム性
        print(f"[ML] フォールバック推薦を適用")
        recommendations = []
        
        # 上位候補を取得
        top_candidates = candidates_sorted[:min(len(candidates_sorted), num_recommendations * 2)]
        
        for i, candidate in enumerate(top_candidates):
            if len(recommendations) >= num_recommendations:
                break
            
            # 軽いランダム性を適用
            if randomness > 0 and random.random() < randomness:
                # 時々、少し下位の候補も選ぶ
                random_index = random.randint(0, min(len(top_candidates) - 1, i + 5))
                selected_candidate = top_candidates[random_index]
            else:
                selected_candidate = candidate
            
            # 重複チェック
            if not any(rec['title'] == selected_candidate['title'] for rec in recommendations):
                recommendations.append(self.format_recommendation(selected_candidate))
        
        return recommendations

    def apply_diversity_selection(
        self, 
        candidates: List[Dict], 
        num_recommendations: int, 
        diversity_factor: float, 
        randomness: float
    ) -> List[Dict[Any, Any]]:
        """多様性選択"""
        
        # カテゴリ別に分類
        categories = defaultdict(list)
        for candidate in candidates:
            categories[candidate['category']].append(candidate)
        
        print(f"[ML] カテゴリ別候補数: {[(cat, len(cands)) for cat, cands in categories.items()]}")
        
        recommendations = []
        category_list = list(categories.keys())
        
        # 各カテゴリから均等に選択
        max_per_category = max(1, num_recommendations // len(category_list))
        
        for category in category_list:
            category_candidates = categories[category]
            
            # カテゴリ内での選択数
            to_select = min(max_per_category, len(category_candidates))
            
            for i in range(to_select):
                if len(recommendations) >= num_recommendations:
                    break
                
                if i < len(category_candidates):
                    candidate = category_candidates[i]
                    
                    # ランダム性を適用
                    if randomness > 0 and random.random() < randomness and i + 1 < len(category_candidates):
                        # 時々、カテゴリ内の次の候補を選ぶ
                        candidate = category_candidates[i + 1]
                    
                    recommendations.append(self.format_recommendation(candidate))
        
        # 残りの枠を埋める
        all_remaining = [c for c in candidates if not any(rec['title'] == c['title'] for rec in recommendations)]
        
        while len(recommendations) < num_recommendations and all_remaining:
            candidate = all_remaining.pop(0)
            recommendations.append(self.format_recommendation(candidate))
        
        return recommendations

    def format_recommendation(self, candidate: Dict) -> Dict[Any, Any]:
        """推薦結果のフォーマット"""
        book = candidate['book_data']
        return {
            'title': book.get('title', ''),
            'authors': book.get('authors', []),
            'description': book.get('description', ''),
            'image': book.get('image', ''),
            'rating': book.get('rating', 0),
            'google_id': book.get('google_id', ''),
            'ml_similarity_score': candidate['similarity_score'],
            'category': candidate['category'],
            'recommendation_reason': f"類似度: {candidate['similarity_score']:.3f} | カテゴリ: {candidate['category']}",
            'algorithm': 'TF-IDF + Cosine Similarity + Flexible Diversity'
        }

# グローバルインスタンス
ml_recommender = MLBookRecommender()

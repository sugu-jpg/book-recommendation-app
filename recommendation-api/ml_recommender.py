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
            min_df=1,          # 最小文書頻度：1つの文書にでも出現すればOK
            max_df=1.0,        # 最大文書頻度：すべての文書に出現してもOK
            token_pattern=r'(?u)\b\w+\b',  # 日本語対応
            lowercase=True,
            strip_accents=None
        )
        self.book_vectors = None
        self.book_data = []
        self.feature_names = []
        
    def preprocess_text(self, title: str, description: str = "", use_title: bool = False) -> str:
        """改善されたテキストの前処理"""
        print(f"[ML] 前処理開始: {title[:30]}...")
        print(f"[ML] 説明文の長さ: {len(description) if description else 0}")
        
        # ハイブリッドアプローチ：説明文が空の場合はタイトルを使用
        if use_title:
            # タイトル + 説明
            if title is None:
                title = ""
            if description is None:
                description = ""
            combined_text = f"{title} {description}"
        else:
            # 説明文が空の場合はタイトルを使用
            if description is None:
                description = ""
            
            if description.strip():
                combined_text = description
                print(f"[ML] 説明文を使用")
            else:
                # フォールバック: 説明文が空の場合はタイトルを使用
                combined_text = title if title else ""
                print(f"[ML] 説明文が空のため、タイトルを使用: {title}")
        
        print(f"[ML] 結合テキスト: {combined_text[:50]}...")
        
        # 巻数除去
        cleaned = re.sub(r'[0-9]+巻|第[0-9]+巻|vol\.?\s*[0-9]+|[0-9]+$', '', combined_text)
        # 特殊版の表記除去
        cleaned = re.sub(r'モノクロ版|カラー版|完全版|新装版', '', cleaned)
        # 特殊文字除去
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        # 余分な空白除去
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        result = cleaned.lower()
        print(f"[ML] 前処理結果: '{result}'")
        return result
    
    def create_book_corpus(self, all_books: List[Dict[Any, Any]], use_title: bool = False) -> List[str]:
        """全ての本からコーパスを作成"""
        print(f"[ML] コーパス作成開始 - 対象本数: {len(all_books)}")
        print(f"[ML] use_title設定: {use_title}")
        
        corpus = []
        self.book_data = []
        
        for i, book in enumerate(all_books):
            title = book.get('title', '') or ''
            description = book.get('description', '') or ''
            
            print(f"[ML] 本 {i}: タイトル='{title}', 説明文の長さ={len(description)}")
            
            # テキスト前処理（use_titleパラメータを渡す）
            processed_text = self.preprocess_text(title, description, use_title=use_title)
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
        
        # 空でないコーパスの数を確認
        non_empty_count = sum(1 for text in corpus if text and text.strip())
        print(f"[ML] 空でないコーパス数: {non_empty_count}")
        
        return corpus
    
    def fit_tfidf(self, corpus: List[str]):
        """TF-IDFモデルの学習"""
        print(f"[ML] TF-IDF学習開始 - コーパスサイズ: {len(corpus)}")
        
        # デバッグ: コーパスの内容を確認
        print(f"[ML] コーパスの最初の5つ:")
        for i, text in enumerate(corpus[:5]):
            print(f"[ML]   {i}: '{text}' (長さ: {len(text)})")
        
        try:
            # 空のテキストを除外
            valid_corpus = [text for text in corpus if text and text.strip()]
            
            print(f"[ML] 有効なコーパス数: {len(valid_corpus)}")
            print(f"[ML] 有効なコーパスの最初の3つ:")
            for i, text in enumerate(valid_corpus[:3]):
                print(f"[ML]   {i}: '{text}' (長さ: {len(text)})")
            
            # 条件を緩和：1つでも有効なコーパスがあれば処理を続行
            if len(valid_corpus) < 1:
                print(f"[ML] 警告: 有効なコーパスが0個です")
                # 最小限のTF-IDFモデルを作成
                self.book_vectors = np.zeros((len(corpus), 10))
                self.feature_names = ['dummy'] * 10
                return
            
            # 1つだけの場合の特別処理
            if len(valid_corpus) == 1:
                print(f"[ML] 警告: 有効なコーパスが1個のみです - 簡単なベクトル化を実行")
                # 単純な単語ベースのベクトル化
                words = valid_corpus[0].split()
                if len(words) == 0:
                    self.book_vectors = np.zeros((len(corpus), 10))
                    self.feature_names = ['dummy'] * 10
                    return
                
                # 簡単な単語ベクトル化
                unique_words = list(set(words))[:100]  # 最大100単語
                self.feature_names = unique_words
                
                # 各文書を単語頻度でベクトル化
                vectors = []
                for text in corpus:
                    if text and text.strip():
                        text_words = text.split()
                        vector = [text_words.count(word) for word in unique_words]
                    else:
                        vector = [0] * len(unique_words)
                    vectors.append(vector)
                
                self.book_vectors = np.array(vectors)
                print(f"[ML] 簡単なベクトル化完了 - 形状: {self.book_vectors.shape}")
                print(f"[ML] 特徴語数: {len(self.feature_names)}")
                return
            
            # 通常のTF-IDFベクトル化
            self.book_vectors = self.tfidf_vectorizer.fit_transform(valid_corpus)
            self.feature_names = self.tfidf_vectorizer.get_feature_names_out()
            
            print(f"[ML] TF-IDFベクトル形状: {self.book_vectors.shape}")
            print(f"[ML] 抽出された特徴語数: {len(self.feature_names)}")
            
            # 特徴語をいくつか表示
            if len(self.feature_names) > 0:
                print(f"[ML] 特徴語の例: {self.feature_names[:10]}")
            
        except Exception as e:
            print(f"[ML] TF-IDF学習エラー: {e}")
            import traceback
            traceback.print_exc()
            # フォールバック
            self.book_vectors = np.zeros((len(corpus), 10))
            self.feature_names = ['dummy'] * 10
    
    def calculate_hybrid_score(
        self,
        candidate_book: Dict[Any, Any],
        user_books: List[Dict[Any, Any]],
        tfidf_score: float,
        weights: Dict[str, float] = None
    ) -> Tuple[float, Dict[str, float]]:
        """ハイブリッドスコアを計算（TF-IDF + 著者 + ジャンル + 人気度）"""
        
        if weights is None:
            weights = {
                'tfidf': 0.4,      # TF-IDFの重み
                'author': 0.3,     # 著者マッチングの重み
                'genre': 0.4,      # ジャンルマッチングの重み
                'popularity': 0.3  # 人気度の重み
            }
        
        # 1. 著者マッチングスコア
        author_score = 0.0
        candidate_authors = set(candidate_book.get('authors', []))
        if candidate_authors:
            for user_book in user_books:
                user_authors = set(user_book.get('authors', []))
                if user_authors and candidate_authors & user_authors:  # 共通の著者がいる
                    author_score = 1.0
                    print(f"[ML] 著者マッチ: {candidate_authors & user_authors}")
                    break
        
        # 2. ジャンル/カテゴリマッチングスコア
        genre_score = 0.0
        candidate_categories = set(candidate_book.get('categories', []))
        if candidate_categories:
            user_categories = set()
            for user_book in user_books:
                user_categories.update(user_book.get('categories', []))
            
            if user_categories:
                # ジャカード類似度
                intersection = candidate_categories & user_categories
                union = candidate_categories | user_categories
                if union:
                    genre_score = len(intersection) / len(union)
                    if intersection:
                        print(f"[ML] ジャンルマッチ: {intersection}")
        
        # 3. 人気度スコア（評価の正規化）
        popularity_score = 0.0
        rating = candidate_book.get('rating', 0)
        if rating > 0:
            # 評価を0-1に正規化（5点満点と仮定）
            popularity_score = min(rating / 5.0, 1.0)
        else:
            popularity_score = 0.5  # 評価がない場合は中間値
        
        # 4. ハイブリッドスコアの計算
        hybrid_score = (
            tfidf_score * weights['tfidf'] +
            author_score * weights['author'] +
            genre_score * weights['genre'] +
            popularity_score * weights['popularity']
        )
        
        # デバッグ情報
        score_breakdown = {
            'tfidf': tfidf_score,
            'author': author_score,
            'genre': genre_score,
            'popularity': popularity_score,
            'hybrid': hybrid_score
        }
        
        return hybrid_score, score_breakdown
    
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
        randomness: float = 0.2,
        use_title_in_tfidf: bool = True,  # 新しいパラメータ
        filter_same_series: bool = True    # 新しいパラメータ
    ) -> List[Dict[Any, Any]]:
        """改善された推薦機能"""
        print(f"[ML] 推薦開始")
        print(f"[ML] use_title_in_tfidf: {use_title_in_tfidf}")
        print(f"[ML] filter_same_series: {filter_same_series}")
        
        try:
            # 1. 全書籍を結合
            all_books = user_books + external_books
            print(f"[ML] all_books作成後: {len(all_books)}冊")
            
            # 2. コーパス作成（use_title_in_tfidfパラメータを渡す）
            corpus = self.create_book_corpus(all_books, use_title=use_title_in_tfidf)
            self.fit_tfidf(corpus)
            user_profile = self.create_user_profile(user_books)
            
            if user_profile.size == 0:
                print("[ML] ユーザープロファイルが空です")
                return []
                
            similarity_scores = self.calculate_similarity_scores(user_profile)
            
            if not similarity_scores:
                print("[ML] 類似度スコアが空です")
                return []
            
            # 重要: ユーザー本数を明示的に記録
            user_books_count = len(user_books)
            print(f"[ML] ユーザー本のインデックス範囲: 0-{user_books_count-1}")
            print(f"[ML] 外部本のインデックス範囲: {user_books_count}-{len(all_books)-1}")
            
            # 外部本の類似度をチェック
            external_candidates = [(idx, score) for idx, score in similarity_scores if idx >= user_books_count]
            print(f"[ML] 外部本の候補数: {len(external_candidates)}")
            
            # 候補作成
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
                
                # ハイブリッドスコアを計算（TF-IDF + 著者 + ジャンル + 人気度）
                hybrid_score, score_breakdown = self.calculate_hybrid_score(
                    book, user_books, similarity_score
                )
                
                # ハイブリッドスコアの閾値（より緩い）
                if hybrid_score < 0.01:
                    print(f"[ML] ハイブリッドスコアが低いため除外: {book_title} (スコア: {hybrid_score:.4f})")
                    continue
                
                # 有効な候補として追加
                category = self.estimate_category(book)
                
                candidate = {
                    'book_data': book,
                    'similarity_score': float(similarity_score),
                    'hybrid_score': float(hybrid_score),  # ハイブリッドスコアを追加
                    'score_breakdown': score_breakdown,   # スコアの内訳を追加
                    'category': category,
                    'title': book_title
                }
                all_candidates.append(candidate)
                
                # デバッグ出力
                if score_breakdown['author'] > 0 or score_breakdown['genre'] > 0:
                    print(f"[ML] {book_title[:30]}... - ハイブリッド: {hybrid_score:.3f} (TF-IDF: {score_breakdown['tfidf']:.3f}, 著者: {score_breakdown['author']:.3f}, ジャンル: {score_breakdown['genre']:.3f}, 人気: {score_breakdown['popularity']:.3f})")
            
            print(f"[ML] 最終的な有効候補数: {len(all_candidates)}")
            
            # 同じシリーズの除外
            if filter_same_series:
                all_candidates = self.filter_same_series_books(all_candidates, user_books)
            
            # 推薦候補が少ない場合の対処
            if len(all_candidates) == 0:
                print(f"[ML] 外部本候補が0件 - 外部検索を増やす必要があります")
                return []
            
            if len(all_candidates) < num_recommendations:
                print(f"[ML] 候補不足: {len(all_candidates)}件 < {num_recommendations}件")
                return [self.format_recommendation(candidate) for candidate in all_candidates]
            
            # ハイブリッドスコアでソート
            all_candidates.sort(key=lambda x: x['hybrid_score'], reverse=True)
            
            # 推薦生成
            recommendations = all_candidates[:num_recommendations]
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
        score_breakdown = candidate.get('score_breakdown', {})
        
        # 推薦理由を詳細に生成
        reasons = []
        if score_breakdown.get('author', 0) > 0:
            reasons.append("同じ著者")
        if score_breakdown.get('genre', 0) > 0:
            reasons.append("同ジャンル")
        if score_breakdown.get('tfidf', 0) > 0.1:
            reasons.append("内容が似ている")
        if score_breakdown.get('popularity', 0) > 0.7:
            reasons.append("高評価")
        
        reason_text = " | ".join(reasons) if reasons else "おすすめ"
        
        return {
            'title': book.get('title', ''),
            'authors': book.get('authors', []),
            'description': book.get('description', ''),
            'image': book.get('image', ''),
            'rating': book.get('rating', 0),
            'google_id': book.get('google_id', ''),
            'ml_similarity_score': candidate.get('hybrid_score', candidate['similarity_score']),
            'category': candidate['category'],
            'recommendation_reason': reason_text,
            'algorithm': 'Hybrid (TF-IDF + Author + Genre + Popularity)',
            'score_details': {
                'hybrid': candidate.get('hybrid_score', 0),
                'tfidf': score_breakdown.get('tfidf', 0),
                'author': score_breakdown.get('author', 0),
                'genre': score_breakdown.get('genre', 0),
                'popularity': score_breakdown.get('popularity', 0)
            }
        }

    def extract_series_name(self, title: str) -> str:
        """シリーズ名を抽出（より厳格、英語↔日本語統一）"""
        if not title:
            return ""
        
        # 小文字化
        cleaned = title.lower()
        
        # よく知られた英語タイトルを日本語に変換（正規化）
        title_mapping = {
            'one piece': 'ワンピース',
            'onepiece': 'ワンピース',
            'naruto': 'ナルト',
            'bleach': 'ブリーチ',
            'demon slayer': '鬼滅の刃',
            'attack on titan': '進撃の巨人',
            'my hero academia': '僕のヒーローアカデミア',
            'jujutsu kaisen': '呪術廻戦',
            'dragon ball': 'ドラゴンボール',
            'hunter x hunter': 'ハンター×ハンター',
            'death note': 'デスノート',
            'haikyu': 'ハイキュー',
            'slam dunk': 'スラムダンク'
        }
        
        for eng, jpn in title_mapping.items():
            if eng in cleaned:
                cleaned = cleaned.replace(eng, jpn.lower())
        
        # 巻数パターンを除去（より広範囲）
        cleaned = re.sub(r'[0-9]+巻|第[0-9]+巻', '', cleaned)  # ○巻、第○巻
        cleaned = re.sub(r'vol\.?\s*[0-9]+', '', cleaned, flags=re.IGNORECASE)  # vol.1, Vol 1
        cleaned = re.sub(r'\s+[0-9]+\s*$', '', cleaned)  # 末尾のスペース+数字（「ワンピース 1」など）
        cleaned = re.sub(r'\s+[0-9]+\)', '', cleaned)  # 「タイトル 1)」パターン
        cleaned = re.sub(r'[0-9]+$', '', cleaned)  # 末尾の数字のみ（「ワンピース1」など）
        
        # バージョン情報を除去
        cleaned = re.sub(r'モノクロ版|カラー版|完全版|新装版|限定版|特装版', '', cleaned)
        cleaned = re.sub(r'【完全版】|【新装版】|【限定版】', '', cleaned)
        cleaned = re.sub(r'第[一二三四五六七八九十]+巻', '', cleaned)  # 第一巻、第二巻など
        
        # 括弧内を除去（巻数や補足情報が含まれることが多い）
        cleaned = re.sub(r'\([^)]*\)|（[^）]*）|【[^】]*】|\[[^\]]*\]', '', cleaned)
        
        # 余分な空白を除去
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        # 記号を除去
        cleaned = re.sub(r'[!！?？~～\-ー・:]', '', cleaned)
        
        return cleaned

    def is_same_series(self, title1: str, title2: str) -> bool:
        """同じシリーズかどうかを判定（より厳格）"""
        series1 = self.extract_series_name(title1)
        series2 = self.extract_series_name(title2)
        
        # 空または非常に短いタイトルは除外
        if not series1 or not series2 or len(series1) < 2 or len(series2) < 2:
            return False
        
        # 完全一致
        if series1 == series2:
            return True
        
        # 部分一致（85%以上の類似度）
        # 短い方の長さの85%以上が一致する場合
        min_len = min(len(series1), len(series2))
        max_len = max(len(series1), len(series2))
        
        # レーベンシュタイン距離の簡易版：短い方が長い方に含まれる
        if min_len > 3:
            if series1 in series2 or series2 in series1:
                # 含まれているが、長さの差が大きすぎる場合は除外
                if max_len / min_len < 1.5:  # 1.5倍以内
                    return True
        
        return False

    def filter_same_series_books(self, candidates: List[Dict], user_books: List[Dict]) -> List[Dict]:
        """同じシリーズの本を除外"""
        filtered_candidates = []
        
        # ユーザーが読んだ本のシリーズ名を収集
        user_series = set()
        for user_book in user_books:
            user_title = user_book.get('title', '')
            if user_title:
                series_name = self.extract_series_name(user_title)
                if series_name:
                    user_series.add(series_name)
        
        print(f"[ML] ユーザーが読んだシリーズ: {user_series}")
        
        # 候補から同じシリーズを除外
        for candidate in candidates:
            book_title = candidate['book_data'].get('title', '')
            if not book_title:
                continue
            
            candidate_series = self.extract_series_name(book_title)
            
            # 同じシリーズでない場合のみ追加
            if candidate_series not in user_series:
                filtered_candidates.append(candidate)
            else:
                print(f"[ML] 除外: {book_title} (シリーズ: {candidate_series})")
        
        print(f"[ML] シリーズフィルタリング後: {len(filtered_candidates)}件")
        return filtered_candidates

    def calculate_fallback_score(self, book: Dict[Any, Any]) -> float:
        """類似度が0の本に対するフォールバックスコア計算"""
        score = 0.0
        
        # 評価による重み付け
        rating = book.get('rating', 0) or 0
        if rating > 0:
            score += rating * 0.1  # 評価を軽く重み付け
        
        # 説明文がある場合の重み付け
        description = book.get('description', '') or ''
        if description and len(description) > 50:
            score += 0.05  # 説明文がある場合は軽く加点
        
        # 著者情報がある場合の重み付け
        authors = book.get('authors', []) or []
        if authors:
            score += 0.03  # 著者情報がある場合は軽く加点
        
        # 画像がある場合の重み付け
        image = book.get('image', '') or ''
        if image:
            score += 0.02  # 画像がある場合は軽く加点
        
        # 最大値を0.2に制限（機械学習の類似度より低く保つ）
        return min(score, 0.2)

# グローバルインスタンス
ml_recommender = MLBookRecommender()

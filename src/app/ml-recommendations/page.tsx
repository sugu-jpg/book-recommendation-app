"use client";

import { useEffect, useState } from "react";
import { supabase } from "../utils/supabaseClient";
import Link from "next/link";
import Image from "next/image";

type MLRecommendation = {
  google_id: string;
  title: string;
  authors: string[];
  description: string;
  image: string;
  rating: number;
  ml_similarity_score: number;
  recommendation_reason: string;
  algorithm: string;
};

export default function MLRecommendationsPage() {
  const [recommendations, setRecommendations] = useState<MLRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<any>(null);

  useEffect(() => {
    const getUser = async () => {
      const { data } = await supabase.auth.getUser();
      setUser(data.user);
    };
    getUser();
  }, []);

  const fetchMLRecommendations = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: "12",
        diversity: "0.3",
        randomness: "0.2"
      });
      
      const url = `http://localhost:8000/api/ml-recommendations/${user.id}?${params.toString()}`;
      const response = await fetch(url);
      const data = await response.json();
      
      setRecommendations(data.recommendations || []);
    } catch (error) {
      console.error("ML推薦取得エラー:", error);
      alert("推薦の取得に失敗しました。しばらく時間をおいて再度お試しください。");
    }
    setLoading(false);
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-purple-50 to-blue-50">
        <div className="bg-white p-8 rounded-xl shadow-lg">
          <div className="text-center">
            <div className="text-4xl mb-4">🔑</div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">ログインが必要です</h2>
            <p className="text-gray-600 mb-4">機械学習推薦を利用するにはログインしてください</p>
            <Link href="/">
              <button className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors">
                ログインページへ
              </button>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-blue-50 to-indigo-50">
      {/* ヘッダー */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-blue-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-xl">🤖</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">機械学習推薦</h1>
              </div>
            </div>
            
            <Link href="/">
              <button className="bg-gray-500 text-white px-4 py-2 rounded-lg hover:bg-gray-600 transition-all duration-200 transform hover:scale-105 shadow-sm">
                ← 戻る
              </button>
            </Link>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* ML推薦取得セクション */}
        <div className="bg-white rounded-xl shadow-lg p-8 mb-8 border border-gray-100">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-green-400 to-blue-500 rounded-full flex items-center justify-center mx-auto mb-4">
              <span className="text-white font-bold text-2xl">🧠</span>
            </div>
            
            <h2 className="text-2xl font-bold text-gray-800 mb-2">あなたにおすすめの本</h2>
            <p className="text-gray-600 mb-6 max-w-2xl mx-auto">
              機械学習（TF-IDF + コサイン類似度）を使用して、あなたの読書履歴から最適な本を推薦します。
              読書の好みを分析し、新しい発見をお届けします。
            </p>
            
            <button
              onClick={fetchMLRecommendations}
              disabled={loading}
              className="bg-gradient-to-r from-green-500 to-blue-500 text-white py-3 px-8 rounded-lg hover:from-green-600 hover:to-blue-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 transform hover:scale-105 shadow-lg font-medium"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  分析中...
                </div>
              ) : (
                "🤖 おすすめの本を取得"
              )}
            </button>
          </div>

          {/* AI技術説明 */}
          <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 rounded-lg border border-purple-100">
            <h3 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
              <span className="text-purple-600">⚡</span>
              使用している技術
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm text-gray-600">
              <div className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">📊</span>
                <div>
                  <strong>TF-IDF:</strong> 文書内の重要な単語を特定
                </div>
              </div>
              <div className="flex items-start gap-2">
                <span className="text-green-500 mt-0.5">📐</span>
                <div>
                  <strong>コサイン類似度:</strong> 本の内容の類似性を計算
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* 推薦結果 */}
        {recommendations.length > 0 && (
          <div className="mb-6">
            <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center gap-2">
              <span className="text-purple-600">✨</span>
              推薦結果 ({recommendations.length}冊)
            </h3>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendations.map((book, index) => (
            <div 
              key={book.google_id || index} 
              className="bg-white rounded-xl shadow-md hover:shadow-xl transition-all duration-300 transform hover:-translate-y-2 border border-gray-100 overflow-hidden group"
            >
              {book.image && (
                <div className="relative h-48 overflow-hidden">
                  <Image
                    src={book.image}
                    alt={book.title}
                    width={300}
                    height={192}
                    className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/30 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                  
                  {/* 類似度スコアバッジ */}
                  <div className="absolute top-3 right-3">
                    <div className="bg-gradient-to-r from-purple-500 to-blue-500 text-white px-2 py-1 rounded-full text-xs font-bold shadow-lg">
                      類似度 {(book.ml_similarity_score * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
              )}
              
              <div className="p-5">
                <h3 className="font-bold text-lg mb-2 text-gray-800 line-clamp-2 group-hover:text-purple-600 transition-colors">
                  {book.title}
                </h3>
                
                <p className="text-gray-600 text-sm mb-3">
                  📝 {book.authors.join(", ")}
                </p>
                
                {/* ML情報カード */}
                <div className="bg-gradient-to-r from-purple-50 to-blue-50 p-3 rounded-lg mb-3 border border-purple-100">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-xs font-medium text-purple-700 mb-1">
                        🤖 類似度スコア
                      </p>
                      <div className="flex items-center gap-2">
                        <div className="w-full bg-gray-200 rounded-full h-2 max-w-[80px]">
                          <div 
                            className="bg-gradient-to-r from-purple-500 to-blue-500 h-2 rounded-full transition-all duration-500"
                            style={{ width: `${book.ml_similarity_score * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs font-bold text-purple-600">
                          {(book.ml_similarity_score * 100).toFixed(1)}%
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {book.description && (
                  <p className="text-gray-700 text-sm mb-3 line-clamp-3">
                    {book.description.slice(0, 150)}...
                  </p>
                )}
                
                {book.rating > 0 && (
                  <div className="flex items-center gap-1">
                    <span className="text-yellow-500">⭐</span>
                    <span className="text-sm font-medium text-gray-700">{book.rating}/5</span>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* 空状態 */}
        {recommendations.length === 0 && !loading && (
          <div className="text-center py-16">
            <div className="w-24 h-24 bg-gradient-to-r from-purple-100 to-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <span className="text-4xl">🤖</span>
            </div>
            <h3 className="text-2xl font-semibold text-gray-700 mb-2">AI推薦を開始しましょう</h3>
            <p className="text-gray-500 mb-6 max-w-md mx-auto">
              上のボタンを押すと、機械学習があなたの読書履歴を分析して、
              最適な本を推薦します。
            </p>
            <div className="text-sm text-gray-400">
              ✨ 高精度な推薦システムで新しい本との出会いを
            </div>
          </div>
        )}

        {/* 読み込み中のオーバーレイ */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white p-8 rounded-xl shadow-xl text-center">
              <div className="w-16 h-16 border-4 border-purple-200 border-t-purple-500 rounded-full animate-spin mx-auto mb-4"></div>
              <h3 className="text-lg font-semibold text-gray-800 mb-2">分析中...</h3>
              <p className="text-gray-600">あなたの読書履歴を分析しています</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
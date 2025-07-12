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

type MLAnalysis = {
  algorithm: string;
  total_features: number;
  user_profile_dimensions: number;
  corpus_size: number;
  top_user_features: Array<{
    feature: string;
    tfidf_score: number;
  }>;
  ml_explanation: {
    tfidf: string;
    cosine_similarity: string;
    user_profile: string;
    recommendation_process: string;
  };
};

export default function MLRecommendationsPage() {
  const [recommendations, setRecommendations] = useState<MLRecommendation[]>([]);
  const [analysis, setAnalysis] = useState<MLAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<any>(null);
  const [keywords, setKeywords] = useState("");
  const [strategy, setStrategy] = useState("");
  const [mlFeatures, setMlFeatures] = useState(0);

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
        limit: "12"
      });
      
      if (keywords.trim()) {
        params.append("keywords", keywords.trim());
      }
      
      const url = `http://localhost:8000/api/ml-recommendations/${user.id}?${params.toString()}`;
      console.log("ML推薦リクエストURL:", url);
      
      const response = await fetch(url);
      console.log("ML推薦レスポンス状態:", response.status);
      
      const data = await response.json();
      console.log("ML推薦レスポンスデータ:", data);
      
      // デバッグ情報を表示
      alert(`レスポンス確認:
      - ステータス: ${response.status}
      - 推薦数: ${data.recommendations ? data.recommendations.length : 0}
      - エラー: ${data.error || "なし"}`);
      
      setRecommendations(data.recommendations || []);
      setStrategy(data.strategy || "");
      setMlFeatures(data.ml_features || 0);
      
      console.log("設定された推薦数:", data.recommendations ? data.recommendations.length : 0);
    } catch (error) {
      console.error("ML推薦取得エラー:", error);
      alert("ML推薦取得エラー: " + error);
    }
    setLoading(false);
  };

  const fetchMLAnalysis = async () => {
    if (!user) return;
    
    try {
      const response = await fetch(`http://localhost:8000/api/ml-analysis/${user.id}`);
      const data = await response.json();
      setAnalysis(data);
    } catch (error) {
      console.error("ML分析取得エラー:", error);
    }
  };

  if (!user) {
    return <div className="p-4">ログインが必要です</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">🤖 機械学習推薦</h1>
          <Link href="/">
            <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
              ← 戻る
            </button>
          </Link>
        </div>

        {/* ML設定セクション */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">🧠 機械学習設定</h2>
          
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                追加キーワード（オプション）
              </label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="例: バトル, 学園, コメディ"
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <p className="text-xs text-gray-500 mt-1">
                外部検索のキーワードを指定できます
              </p>
            </div>

            <div className="flex gap-4">
              <button
                onClick={fetchMLRecommendations}
                disabled={loading}
                className="bg-green-500 text-white py-2 px-6 rounded hover:bg-green-600 disabled:opacity-50"
              >
                {loading ? "ML分析中..." : "🤖 機械学習推薦を取得"}
              </button>
              
              <button
                onClick={fetchMLAnalysis}
                className="bg-purple-500 text-white py-2 px-6 rounded hover:bg-purple-600"
              >
                📊 ML分析を表示
              </button>
              <button
                onClick={async () => {
                  try {
                    const response = await fetch(`http://localhost:8000/api/test-ml/${user.id}`);
                    const data = await response.json();
                    console.log("テスト結果:", data);
                    alert(JSON.stringify(data, null, 2));
                  } catch (error) {
                    console.error("テストエラー:", error);
                    alert("テストエラー: " + error);
                  }
                }}
                className="bg-orange-500 text-white py-2 px-6 rounded hover:bg-orange-600"
              >
                🔧 接続テスト
              </button>
              <button
                onClick={async () => {
                  try {
                    const response = await fetch(`http://localhost:8000/api/debug-recommendations/${user.id}`);
                    const data = await response.json();
                    console.log("デバッグ結果:", data);
                    
                    alert(`デバッグ結果:
                    スコア0の本: ${data.total_zero_books}件
                    高スコアの本: ${data.total_high_books}件
                    
                    あなたの重要キーワード:
                    ${data.user_top_features.map(f => f.feature).join(', ')}
                    
                    詳細はコンソールを確認してください`);
                  } catch (error) {
                    console.error("デバッグエラー:", error);
                  }
                }}
                className="bg-red-500 text-white py-2 px-6 rounded hover:bg-red-600"
              >
                🔍 類似度デバッグ
              </button>
            </div>
          </div>
        </div>

        {/* ML分析結果 */}
        {analysis && (
          <div className="bg-blue-50 p-6 rounded-lg mb-6">
            <h3 className="text-lg font-semibold mb-4">📊 機械学習分析結果</h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
              <div className="bg-white p-4 rounded">
                <h4 className="font-medium text-gray-800">TF-IDF統計</h4>
                <p className="text-sm text-gray-600">特徴語数: {analysis.total_features}</p>
                <p className="text-sm text-gray-600">コーパスサイズ: {analysis.corpus_size}</p>
                <p className="text-sm text-gray-600">プロファイル次元: {analysis.user_profile_dimensions}</p>
              </div>
              
              <div className="bg-white p-4 rounded">
                <h4 className="font-medium text-gray-800">あなたの重要キーワード</h4>
                <div className="flex flex-wrap gap-1 mt-2">
                  {analysis.top_user_features.slice(0, 8).map((feature, index) => (
                    <span 
                      key={index}
                      className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                    >
                      {feature.feature} ({feature.tfidf_score.toFixed(3)})
                    </span>
                  ))}
                </div>
              </div>
            </div>
            
            <div className="bg-white p-4 rounded">
              <h4 className="font-medium text-gray-800 mb-2">📚 機械学習の仕組み</h4>
              <div className="text-sm text-gray-600 space-y-1">
                <p><strong>1. TF-IDF:</strong> {analysis.ml_explanation.tfidf}</p>
                <p><strong>2. コサイン類似度:</strong> {analysis.ml_explanation.cosine_similarity}</p>
                <p><strong>3. ユーザープロファイル:</strong> {analysis.ml_explanation.user_profile}</p>
                <p><strong>4. 推薦プロセス:</strong> {analysis.ml_explanation.recommendation_process}</p>
              </div>
            </div>
          </div>
        )}

        {/* 推薦情報 */}
        {strategy && (
          <div className="bg-green-50 p-4 rounded mb-6">
            <h3 className="font-semibold mb-2">🎯 推薦戦略: {strategy}</h3>
            <p className="text-sm text-gray-600">
              抽出されたML特徴語数: {mlFeatures}個
            </p>
          </div>
        )}

        {/* デバッグ情報 */}
        <div className="bg-yellow-50 p-4 rounded mb-6">
          <h3 className="font-semibold mb-2">🔧 デバッグ情報</h3>
          <p className="text-sm text-gray-600">
            推薦配列の長さ: {recommendations.length}
          </p>
          <p className="text-sm text-gray-600">
            ローディング状態: {loading ? "true" : "false"}
          </p>
          <p className="text-sm text-gray-600">
            ユーザーID: {user?.id || "未取得"}
          </p>
        </div>

        {/* 推薦結果 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendations.map((book, index) => (
            <div key={book.google_id || index} className="bg-white rounded-lg shadow-md p-4">
              {book.image && (
                <Image
                  src={book.image}
                  alt={book.title}
                  width={200}
                  height={192}
                  className="w-full h-48 object-cover rounded mb-4"
                />
              )}
              
              <h3 className="font-bold text-lg mb-2">{book.title}</h3>
              
              <p className="text-gray-600 text-sm mb-2">
                著者: {book.authors.join(", ")}
              </p>
              
              {/* ML情報 */}
              <div className="bg-purple-50 p-2 rounded mb-2">
                <p className="text-xs text-purple-700">
                  🤖 {book.algorithm}
                </p>
                <p className="text-xs text-purple-600">
                  類似度スコア: {book.ml_similarity_score.toFixed(4)}
                </p>
              </div>
              
              {book.description && (
                <p className="text-gray-700 text-sm mb-3 line-clamp-3">
                  {book.description.slice(0, 150)}...
                </p>
              )}
              
              {book.rating > 0 && (
                <p className="text-yellow-500 text-sm">
                  ⭐ {book.rating}/5
                </p>
              )}
            </div>
          ))}
        </div>

        {recommendations.length === 0 && !loading && (
          <div className="text-center text-gray-500 mt-10">
            <p>機械学習推薦を取得するにはボタンを押してください</p>
            <p className="text-sm mt-2">TF-IDF + コサイン類似度による高精度推薦</p>
          </div>
        )}
      </div>
    </div>
  );
}
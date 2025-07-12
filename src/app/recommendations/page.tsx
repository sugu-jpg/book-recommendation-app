"use client";

import { useEffect, useState } from "react";
import { supabase } from "../utils/supabaseClient";
import Link from "next/link";
import Image from "next/image";

type Recommendation = {
  google_id: string;
  title: string;
  authors: string[];
  description: string;
  image: string;
  categories: string[];
  rating: number;
};

type QueryInfo = {
  query: string;
  type: string;
  found: number;
};

export default function RecommendationsPage() {
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState<any>(null);
  
  // 状態
  const [keywords, setKeywords] = useState("");
  const [contentType, setContentType] = useState("auto");
  const [weightBalance, setWeightBalance] = useState(0.5);
  const [preferVolumeOne, setPreferVolumeOne] = useState(true); // 新しく追加
  const [queryInfo, setQueryInfo] = useState<QueryInfo[]>([]);
  const [strategy, setStrategy] = useState("");

  useEffect(() => {
    const getUser = async () => {
      const { data } = await supabase.auth.getUser();
      setUser(data.user);
    };
    getUser();
  }, []);

  const fetchRecommendations = async () => {
    if (!user) return;
    
    setLoading(true);
    try {
      const params = new URLSearchParams({
        limit: "12",
        content_type: contentType,
        weight_balance: weightBalance.toString(),
        prefer_volume_one: preferVolumeOne.toString() // 新しく追加
      });
      
      if (keywords.trim()) {
        params.append("keywords", keywords.trim());
      }
      
      const url = `http://localhost:8000/api/recommendations/${user.id}?${params.toString()}`;
      const response = await fetch(url);
      const data = await response.json();
      
      setRecommendations(data.recommendations || []);
      setQueryInfo(data.query_info || []);
      setStrategy(data.strategy || "");
    } catch (error) {
      console.error("レコメンド取得エラー:", error);
    }
    setLoading(false);
  };

  if (!user) {
    return <div className="p-4">ログインが必要です</div>;
  }

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold">📚 1巻優先推薦</h1>
          <Link href="/">
            <button className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
              ← 戻る
            </button>
          </Link>
        </div>

        {/* 設定セクション */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-xl font-semibold mb-4">🎯 推薦設定</h2>
          
          <div className="space-y-4">
            {/* コンテンツタイプ選択 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                コンテンツタイプ
              </label>
              <select
                value={contentType}
                onChange={(e) => setContentType(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="auto">自動判定</option>
                <option value="manga">漫画・コミック</option>
                <option value="light_novel">ライトノベル</option>
                <option value="novel">小説・文庫</option>
                <option value="general">その他</option>
              </select>
            </div>

            {/* 1巻優先オプション */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferVolumeOne}
                  onChange={(e) => setPreferVolumeOne(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm font-medium text-gray-700">
                  1巻を優先して推薦（推奨）
                </span>
              </label>
              <p className="text-xs text-gray-500 mt-1">
                続巻ではなく、シリーズの第1巻を優先的に推薦します
              </p>
            </div>

            {/* キーワード入力 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                希望キーワード（カンマ区切り）
              </label>
              <input
                type="text"
                value={keywords}
                onChange={(e) => setKeywords(e.target.value)}
                placeholder="例: バトル, 学園, コメディ"
                className="w-full px-3 py-2 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* 重みバランス */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                推薦バランス: {weightBalance === 0 ? "キーワードのみ" : 
                           weightBalance === 1 ? "登録本のみ" : 
                           "ハイブリッド"}
              </label>
              <input
                type="range"
                min="0"
                max="1"
                step="0.1"
                value={weightBalance}
                onChange={(e) => setWeightBalance(parseFloat(e.target.value))}
                className="w-full"
              />
              <div className="flex justify-between text-sm text-gray-500 mt-1">
                <span>キーワード重視</span>
                <span>バランス</span>
                <span>登録本重視</span>
              </div>
            </div>

            {/* 検索ボタン */}
            <button
              onClick={fetchRecommendations}
              disabled={loading}
              className="w-full bg-green-500 text-white py-3 rounded hover:bg-green-600 disabled:opacity-50"
            >
              {loading ? "分析中..." : "1巻優先推薦を取得"}
            </button>
          </div>
        </div>

        {/* 検索情報表示 */}
        {queryInfo.length > 0 && (
          <div className="bg-blue-50 p-4 rounded mb-6">
            <h3 className="font-semibold mb-2">検索戦略: {strategy}</h3>
            <div className="space-y-1">
              {queryInfo.map((info, index) => (
                <div key={index} className="text-sm">
                  <span className="font-medium">{info.type}:</span> {info.query} 
                  <span className="text-gray-600"> ({info.found}件)</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 推薦結果 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {recommendations.map((book) => (
            <div key={book.google_id} className="bg-white rounded-lg shadow-md p-4">
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
              {book.categories.length > 0 && (
                <p className="text-blue-600 text-xs mb-2">
                  {book.categories.slice(0, 2).join(", ")}
                </p>
              )}
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
            推薦を取得するにはボタンを押してください
          </div>
        )}
      </div>
    </div>
  );
}

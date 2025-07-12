"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Image from "next/image";
import { supabase } from "../utils/supabaseClient";
import { Button } from "@/components/ui/button";

// Google Booksの検索結果の型定義
type BookItem = {
  id: string;
  volumeInfo: {
    title: string;
    authors?: string[];
    description?: string;
    imageLinks?: {
      thumbnail?: string;
    };
    averageRating?: number;
    ratingsCount?: number;
    publishedDate?: string;
    pageCount?: number;
    categories?: string[];
  };
};

export default function AddBookPage() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState("");
  const [rating, setRating] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<BookItem[]>([]);
  const [prioritizeFirstVolume, setPrioritizeFirstVolume] = useState(true);
  const [excludeVariants, setExcludeVariants] = useState(true);
  const router = useRouter();

  const buildSmartSearchQuery = (searchTerm: string) => {
    /**
     * より精密な検索クエリを構築
     */
    const hasVolumeNumber = /[0-9]+巻|第[0-9]+巻|vol\.?\s*[0-9]+/i.test(searchTerm);
    
    if (!hasVolumeNumber) {
      // 巻数がない場合、複数の検索パターンを組み合わせ
      return [
        `intitle:"${searchTerm}"`,  // 完全一致優先
        `intitle:"${searchTerm} 1"`, // 1巻
        `intitle:"${searchTerm} 第1巻"`, // 第1巻
        searchTerm  // 通常検索
      ].join(' OR ');
    }
    
    return searchTerm;
  };

  const calculateRelevanceScore = (item: BookItem, searchTerm: string) => {
    /**
     * 関連性スコアを計算（高いほど優先）
     */
    let score = 0;
    const title = item.volumeInfo.title?.toLowerCase() || '';
    const searchLower = searchTerm.toLowerCase();
    
    // 1. タイトル一致度
    if (title === searchLower) score += 1000; // 完全一致
    if (title.startsWith(searchLower)) score += 500; // 前方一致
    if (title.includes(searchLower)) score += 200; // 部分一致
    
    // 2. 1巻判定（最優先）
    const volumeOnePatterns = [
      /^(.+?)\s*1$/, // タイトル末尾が1
      /^(.+?)\s*第1巻/, // 第1巻
      /^(.+?)\s*1巻/, // 1巻
      /^(.+?)\s*一巻/, // 一巻
      /vol\.?\s*1$/i, // Vol.1
      /#1$/i, // #1
      /\s1\s*$/ // 末尾スペース1
    ];
    
    const isVolumeOne = volumeOnePatterns.some(pattern => pattern.test(title));
    if (isVolumeOne) score += 800;
    
    // 3. 知名度（評価数とレビュー数）
    const ratingsCount = item.volumeInfo.ratingsCount || 0;
    const averageRating = item.volumeInfo.averageRating || 0;
    
    score += ratingsCount * 2; // 評価数
    score += averageRating * 10; // 平均評価
    
    // 4. 完全版・特別版の減点
    const variants = ['完全版', 'カラー版', '新装版', '愛蔵版', '特装版', '4コマ', 'ショート', 'アンソロジー', '番外編', 'スピンオフ'];
    if (variants.some(variant => title.includes(variant.toLowerCase()))) {
      score -= 300;
    }
    
    // 5. 著者・画像の有無
    if (item.volumeInfo.authors?.length) score += 50;
    if (item.volumeInfo.imageLinks?.thumbnail) score += 30;
    
    // 6. 出版年（新しいほど良い、でも重みは軽め）
    const publishedYear = item.volumeInfo.publishedDate ? 
      parseInt(item.volumeInfo.publishedDate.split('-')[0]) : 2000;
    if (publishedYear > 2010) score += (publishedYear - 2010);
    
    return score;
  };

  const shouldExcludeItem = (item: BookItem, searchTerm: string) => {
    /**
     * 除外すべきアイテムかどうか判定
     */
    if (!excludeVariants) return false;
    
    const title = item.volumeInfo.title?.toLowerCase() || '';
    
    // 除外キーワード
    const excludeKeywords = [
      '4コマ', 'よんこま', 'ショート', 'アンソロジー', '番外編', 
      'スピンオフ', 'side story', 'サイドストーリー', 'ファンブック',
      'ガイドブック', '公式ガイド', '設定資料', 'アートブック'
    ];
    
    return excludeKeywords.some(keyword => title.includes(keyword));
  };

  const handleSearch = async () => {
    if (!searchTerm) return;
    
    try {
      const smartQuery = buildSmartSearchQuery(searchTerm);
      
      // 多めに取得してから精密フィルタリング
      const res = await fetch(
        `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(smartQuery)}&maxResults=40&orderBy=relevance&langRestrict=ja`
      );

      const data = await res.json();
      
      if (!data.items || data.items.length === 0) {
        setSearchResults([]);
        return;
      }
      
      // フィルタリングとスコアリング
      let processedResults = data.items
        .filter((item: BookItem) => !shouldExcludeItem(item, searchTerm))
        .map((item: BookItem) => ({
          ...item,
          relevanceScore: calculateRelevanceScore(item, searchTerm)
        }))
        .sort((a: any, b: any) => b.relevanceScore - a.relevanceScore)
        .slice(0, 15); // 上位15件に絞る
      
      // 1巻優先オプションが有効な場合
      if (prioritizeFirstVolume) {
        processedResults = processedResults.sort((a: any, b: any) => {
          const titleA = a.volumeInfo.title?.toLowerCase() || '';
          const titleB = b.volumeInfo.title?.toLowerCase() || '';
          
          const isVolumeOneA = /1$|第1巻|1巻|一巻|vol\.?\s*1|#1$/i.test(titleA);
          const isVolumeOneB = /1$|第1巻|1巻|一巻|vol\.?\s*1|#1$/i.test(titleB);
          
          if (isVolumeOneA && !isVolumeOneB) return -1;
          if (!isVolumeOneA && isVolumeOneB) return 1;
          
          return b.relevanceScore - a.relevanceScore;
        });
      }
      
      setSearchResults(processedResults);
      
    } catch (error) {
      console.error('検索エラー:', error);
      setSearchResults([]);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    try {
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        alert("ログインが必要です");
        return;
      }

      const response = await fetch("/api/books", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title,
          description,
          image,
          rating,
          user_id: user.id,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        console.error("API Error:", errorData);
        alert(`エラーが発生しました: ${errorData.message || 'Unknown error'}`);
        return;
      }

      const result = await response.json();
      console.log("Book created:", result);
      
      router.push("/");
    } catch (error) {
      console.error("Submit error:", error);
      alert("送信中にエラーが発生しました");
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-xl mx-auto bg-white p-6 rounded-xl shadow-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">📘 本を追加</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              タイトル <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="例: 君の名は"
              required
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              説明
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="本の説明を入力（任意）"
              rows={4}
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              画像URL（任意）
            </label>
            <input
              type="text"
              value={image}
              onChange={(e) => setImage(e.target.value)}
              placeholder="https://example.com/image.jpg"
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              評価（1〜5）
            </label>
            <select
              value={rating ?? ""}
              onChange={(e) => setRating(Number(e.target.value))}
              className="w-full border border-gray-300 rounded px-3 py-2"
            >
              <option value="">選択してください</option>
              <option value={1}>★☆☆☆☆（1）</option>
              <option value={2}>★★☆☆☆（2）</option>
              <option value={3}>★★★☆☆（3）</option>
              <option value={4}>★★★★☆（4）</option>
              <option value={5}>★★★★★（5）</option>
            </select>
          </div>

          <div className="flex justify-between pt-4">
            <Button
              variant="outline"
              type="button"
              onClick={() => router.back()}
            >
              ← 戻る
            </Button>
            <button
              type="submit"
              className="bg-green-500 text-white px-6 py-2 rounded hover:bg-green-600 transition"
            >
              登録
            </button>
          </div>
        </form>

        {/* 🔽 改善された書籍検索セクション */}
        <div className="mt-10">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            書籍検索（精密検索）
          </label>
          
          {/* 検索オプション */}
          <div className="flex gap-4 mb-3">
            <div className="flex items-center">
              <input
                type="checkbox"
                id="prioritizeFirstVolume"
                checked={prioritizeFirstVolume}
                onChange={(e) => setPrioritizeFirstVolume(e.target.checked)}
                className="mr-1"
              />
              <label htmlFor="prioritizeFirstVolume" className="text-sm">1巻を優先</label>
            </div>
            <div className="flex items-center">
              <input
                type="checkbox"
                id="excludeVariants"
                checked={excludeVariants}
                onChange={(e) => setExcludeVariants(e.target.checked)}
                className="mr-1"
              />
              <label htmlFor="excludeVariants" className="text-sm">4コマ・番外編を除外</label>
            </div>
          </div>
          
          <div className="flex gap-2">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="例: 鋼の錬金術師"
              className="flex-1 border border-gray-300 rounded px-3 py-2"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <button
              type="button"
              onClick={handleSearch}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              精密検索
            </button>
          </div>

          <ul className="mt-4 space-y-4">
            {searchResults.map((item) => {
              const info = item.volumeInfo;
              return (
                <li
                  key={item.id}
                  className="p-4 bg-gray-50 rounded shadow-sm cursor-pointer hover:bg-gray-100 transition border"
                  onClick={() => {
                    setTitle(info.title || "");
                    setDescription(info.description || "");
                    setImage(info.imageLinks?.thumbnail || "");
                  }}
                >
                  <div className="flex gap-3">
                    {info.imageLinks?.thumbnail && (
                      <Image
                        src={info.imageLinks.thumbnail}
                        alt={info.title || ""}
                        width={64}
                        height={96}
                        className="object-cover rounded"
                      />
                    )}
                    <div className="flex-1">
                      <p className="font-bold text-gray-800">{info.title}</p>
                      <p className="text-sm text-gray-600">
                        著者: {info.authors?.join(", ") || "不明"}
                      </p>
                      {info.averageRating && (
                        <p className="text-xs text-yellow-600">
                          ⭐ {info.averageRating}/5 ({info.ratingsCount || 0}件の評価)
                        </p>
                      )}
                      {info.publishedDate && (
                        <p className="text-xs text-gray-500">
                          出版: {info.publishedDate}
                        </p>
                      )}
                      <p className="text-blue-500 text-sm mt-1">
                        📖 クリックしてフォームに反映
                      </p>
                    </div>
                  </div>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}

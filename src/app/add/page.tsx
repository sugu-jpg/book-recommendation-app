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
  };
};

export default function AddBookPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<BookItem[]>([]);
  const [rating, setRating] = useState<number | undefined>(undefined);
  const [prioritizeFirstVolume, setPrioritizeFirstVolume] = useState(false);

  const handleSearch = async () => {
    if (!searchTerm) return;
    
    // 検索語の自動補完：マンガなので1巻を優先したい場合の対策
    let searchQuery = searchTerm;
    const hasVolumeNumber = /[0-9一二三四五六七八九十百]巻|[0-9]+$|vol\.?[0-9]+/i.test(searchTerm);
    
    // 数字を含まない場合、第1巻も検索対象に含める
    if (!hasVolumeNumber) {
      // 元の検索語と「第1巻」を含む検索語の両方を検索する
      searchQuery = `${searchTerm} OR intitle:"${searchTerm} 1" OR intitle:"${searchTerm}1" OR intitle:"${searchTerm} 第1巻"`;
    }
    
    // 検索クエリを送信
    const res = await fetch(
      `https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(searchQuery)}&maxResults=20&orderBy=relevance`
    );

    const data = await res.json();
    
    if (!data.items || data.items.length === 0) {
      setSearchResults([]);
      return;
    }
    
    // 検索結果の後処理と並べ替え
    const sortedResults = [...data.items].sort((a, b) => {
      const titleA = a.volumeInfo.title.toLowerCase();
      const titleB = b.volumeInfo.title.toLowerCase();
      const searchTermLower = searchTerm.toLowerCase();
      
      // 1巻かどうかのチェック（より強力なパターン）
      const isVolumeOneA = /巻?1$|第1巻|第一巻|1巻|一巻|vol\.?\s?1|#1$|volume 1/i.test(titleA);
      const isVolumeOneB = /巻?1$|第1巻|第一巻|1巻|一巻|vol\.?\s?1|#1$|volume 1/i.test(titleB);
      
      // 1巻を最優先
      if (isVolumeOneA && !isVolumeOneB) return -1;
      if (!isVolumeOneA && isVolumeOneB) return 1;
      
      // タイトルが検索語で始まるものを優先
      const startsWithA = titleA.startsWith(searchTermLower);
      const startsWithB = titleB.startsWith(searchTermLower);
      
      if (startsWithA && !startsWithB) return -1;
      if (!startsWithA && startsWithB) return 1;
      
      // 条件2: "第1巻"や"1巻"、"volume 1"などの文字列を含むものを優先
      const volumeOneRegexJP = /(第?1巻|1$|一巻|一$)/i;
      const volumeOneRegexEN = /(volume 1$|vol\.? 1$|book 1$|#1$|part 1$)/i;
      
      const isFirstVolumeA = 
        volumeOneRegexJP.test(titleA) || volumeOneRegexEN.test(titleA);
      const isFirstVolumeB = 
        volumeOneRegexJP.test(titleB) || volumeOneRegexEN.test(titleB);
      
      if (isFirstVolumeA && !isFirstVolumeB) return -1;
      if (!isFirstVolumeA && isFirstVolumeB) return 1;
      
      // 条件3: 著者名が存在するものを優先
      const hasAuthorsA = !!a.volumeInfo.authors?.length;
      const hasAuthorsB = !!b.volumeInfo.authors?.length;
      
      if (hasAuthorsA && !hasAuthorsB) return -1;
      if (!hasAuthorsA && hasAuthorsB) return 1;
      
      // 条件4: 画像が存在するものを優先
      const hasImageA = !!a.volumeInfo.imageLinks?.thumbnail;
      const hasImageB = !!b.volumeInfo.imageLinks?.thumbnail;
      
      if (hasImageA && !hasImageB) return -1;
      if (!hasImageA && hasImageB) return 1;
      
      return 0;
    });
    
    setSearchResults(sortedResults);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const {
      data: { user },
    } = await supabase.auth.getUser();

    await fetch("/api/books", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title,
        description,
        image,
        rating,
        user_id: user?.id, // ← ここで user_id を送る！
      }),
    });

    // 登録が終わったら一覧ページに戻る
    router.push("/");
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

        {/* 🔽 書籍検索セクション */}
        <div className="mt-10">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            書籍検索（Google Books API）
          </label>
          <div className="flex gap-2">
            <input
              type="text"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="書籍タイトルを入力"
              className="flex-1 border border-gray-300 rounded px-3 py-2"
              onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            />
            <div className="flex items-center mr-2">
              <input
                type="checkbox"
                id="prioritizeFirstVolume"
                checked={prioritizeFirstVolume}
                onChange={(e) => setPrioritizeFirstVolume(e.target.checked)}
                className="mr-1"
              />
              <label htmlFor="prioritizeFirstVolume" className="text-sm">1巻を優先</label>
            </div>
            <button
              type="button"
              onClick={handleSearch}
              className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
            >
              検索
            </button>
          </div>

          <ul className="mt-4 space-y-4">
            {searchResults.map((item) => {
              const info = item.volumeInfo;
              return (
                <li
                  key={item.id}
                  className="p-4 bg-gray-50 rounded shadow-sm cursor-pointer hover:bg-gray-100 transition"
                  onClick={() => {
                    setTitle(info.title || "");
                    setDescription(info.description || "");
                    setImage(info.imageLinks?.thumbnail || "");
                  }}
                >
                  <p className="font-bold text-gray-800">{info.title}</p>
                  <p className="text-sm text-gray-600">
                    {info.authors?.join(", ")}
                  </p>
                  {info.imageLinks?.thumbnail && (
                    <Image
                      src={info.imageLinks.thumbnail}
                      alt={info.title}
                      width={128}
                      height={192}
                      className="mt-2"
                    />
                  )}
                  <p className="text-sm mt-2">
                    {info.description?.slice(0, 100)}...
                  </p>
                  <p className="text-blue-500 text-sm mt-1">
                    クリックしてフォームに反映
                  </p>
                </li>
              );
            })}
          </ul>
        </div>
      </div>
    </div>
  );
}

"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "../utils/supabaseClient";
import { Button } from "@/components/ui/button";

export default function AddBookPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [image, setImage] = useState("");
  const [searchTerm, setSearchTerm] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [rating, setRating] = useState<number | undefined>(undefined);

  const handleSearch = async () => {
    if (!searchTerm) return;
    const res = await fetch(
      `https://www.googleapis.com/books/v1/volumes?q=intitle:${encodeURIComponent(
        searchTerm
      )}`
    );

    const data = await res.json();
    setSearchResults(data.items || []);
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
            />
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
                    <img
                      src={info.imageLinks.thumbnail}
                      alt={info.title}
                      className="mt-2 w-32 h-auto"
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

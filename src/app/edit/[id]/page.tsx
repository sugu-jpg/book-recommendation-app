"use client";

import { use, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useParams } from "next/navigation";

type Book = {
  title: string;
  description?: string;
  image?: string;
  rating?: number;
};

export default function EditBookPage() {
  const { id } = useParams(); // ✅ ここでパラメータ取得（string型）
  const router = useRouter();

  const [book, setBook] = useState<Book>({
    title: "",
    description: "",
    image: "",
    rating: undefined,
  });

  useEffect(() => {
    const fetchBook = async () => {
      const res = await fetch(`/api/books/${id}`);
      const data = await res.json();
      setBook(data.book);
    };
    if (id) fetchBook();
  }, [id]);

  const handleUpdate = async (e: React.FormEvent) => {
    e.preventDefault();
    await fetch(`/api/books/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(book),
    });
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-xl mx-auto bg-white p-6 rounded-xl shadow-md">
        <h2 className="text-2xl font-bold text-gray-800 mb-6">📘 本の編集</h2>
        <form onSubmit={handleUpdate} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              タイトル <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={book.title}
              onChange={(e) => setBook({ ...book, title: e.target.value })}
              placeholder="タイトル"
              required
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              説明
            </label>
            <textarea
              value={book.description}
              onChange={(e) =>
                setBook({ ...book, description: e.target.value })
              }
              placeholder="本の説明"
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
              value={book.image}
              onChange={(e) => setBook({ ...book, image: e.target.value })}
              placeholder="https://example.com/image.jpg"
              className="w-full border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-400"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              評価（1〜5）
            </label>
            <select
              value={book.rating ?? ""}
              onChange={(e) =>
                setBook({ ...book, rating: Number(e.target.value) })
              }
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

          <div className="flex justify-between mt-4">
            <button
              type="button"
              onClick={() => router.back()}
              className="text-gray-600 border border-gray-300 px-4 py-2 rounded hover:bg-gray-100"
            >
              ← 戻る
            </button>

            <button
              type="submit"
              className="bg-blue-500 text-white px-6 py-2 rounded hover:bg-blue-600 transition"
            >
              保存
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { supabase } from "./utils/supabaseClient";
import UserInfo from "./components/UserInfo";
import BookCard from "./components/BookCard";
import SortButton from "./components/SortButton";

type Book = {
  id: number;
  title: string;
  description?: string;
  image?: string;
  rating?: number;
  created_at: string;
};

export default function Home() {
  const [books, setBooks] = useState<Book[]>([]);
  const [user, setUser] = useState<any>(null);
  const [sortBy, setSortBy] = useState<"created_at" | "rating">("created_at");
  const [searchTerm, setSearchTerm] = useState("");

  useEffect(() => {
    const fetchUserAndBooks = async () => {
      const { data } = await supabase.auth.getUser();
      setUser(data.user);

      if (!data.user) {
        setBooks([]);
        return;
      }

      const res = await fetch(`/api/books?user_id=${data.user.id}`);
      const fetched = await res.json();

      let sorted = [...fetched.books];

      if (sortBy === "created_at") {
        sorted.sort(
          (a, b) =>
            new Date(a.created_at).getTime() - new Date(b.created_at).getTime()
        );
      } else if (sortBy === "rating") {
        sorted.sort((a, b) => (b.rating || 0) - (a.rating || 0));
      }

      setBooks(sorted);
    };

    fetchUserAndBooks();
  }, [sortBy]);

  const handleDelete = async (id: number) => {
    const confirm = window.confirm("本当に削除しますか？");
    if (!confirm) return;

    const res = await fetch(`/api/books/${id}`, {
      method: "DELETE",
    });

    if (res.ok) {
      setBooks((prevBooks) => prevBooks.filter((book) => book.id !== id));
    } else {
      alert("削除に失敗しました");
    }
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
    setUser(null);
    setBooks([]);
  };

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col justify-center items-center bg-gray-100">
        <h1 className="text-2xl font-bold mb-4">📚 本棚アプリ</h1>
        <p className="text-gray-600 mb-4">ログインしてください。</p>
        <button
          onClick={() => supabase.auth.signInWithOAuth({ provider: "google" })}
          className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
        >
          Googleでログイン
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-5xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center gap-2">
            <UserInfo />

            <button
              onClick={handleLogout}
              className="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600"
            >
              ログアウト
            </button>
          </div>

          <h1 className="text-2xl font-bold mb-4">📚 本棚アプリ</h1>

          <div className="flex gap-2 flex-wrap">
            <div className="flex gap-2">
              <SortButton
                label="作成順"
                value="created_at"
                current={sortBy}
                onClick={(value) => setSortBy(value)}
              />
              <SortButton
                label="評価順"
                value="rating"
                current={sortBy}
                onClick={(value) => setSortBy(value)}
              />
            </div>

            <input
              type="text"
              placeholder="タイトル検索"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="border border-gray-300 px-3 py-2 rounded max-w-xs"
            />

            <Link href="/add">
              <button className="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600">
                ＋ 本を追加
              </button>
            </Link>
          </div>
        </div>

        <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
          {books
            .filter((book) =>
              book.title.toLowerCase().includes(searchTerm.toLowerCase())
            )
            .map((book) => (
              <BookCard key={book.id} book={book} onDelete={handleDelete} />
            ))}
        </ul>
      </div>
    </div>
  );
}

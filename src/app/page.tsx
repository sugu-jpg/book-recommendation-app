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
  // メール+パスワード認証用のstate
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSignUp, setIsSignUp] = useState(false);
  const [authError, setAuthError] = useState("");

  useEffect(() => {
    // 認証状態の変化を監視
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        setUser(session?.user ?? null);
        
        if (session?.user) {
          // ユーザーがログインした時に本のデータを取得
          await fetchBooks(session.user.id);
        } else {
          // ログアウト時は本のリストをクリア
          setBooks([]);
        }
      }
    );

    // 初回ロード時の認証状態確認
    const getInitialSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      setUser(session?.user ?? null);
      
      if (session?.user) {
        await fetchBooks(session.user.id);
      }
    };

    getInitialSession();

    // クリーンアップ関数
    return () => subscription.unsubscribe();
  }, []);

  // ソート変更時に本のデータを再取得
  useEffect(() => {
    if (user) {
      fetchBooks(user.id);
    }
  }, [sortBy, user]);

  const fetchBooks = async (userId: string) => {
    try {
      const res = await fetch(`/api/books?user_id=${userId}`);
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
    } catch (error) {
      console.error("本のデータの取得に失敗しました:", error);
    }
  };

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

  // メール+パスワードでログイン
  const handleEmailLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    
    try {
      const { error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) {
        setAuthError(error.message);
      }
    } catch (err: any) {
      setAuthError(err.message);
    }
  };

  // 新規ユーザー登録
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError("");
    
    try {
      const { error } = await supabase.auth.signUp({
        email,
        password,
      });
      
      if (error) {
        setAuthError(error.message);
      } else {
        alert("確認メールを送信しました。メールを確認してアカウントを有効化してください。");
      }
    } catch (err: any) {
      setAuthError(err.message);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex flex-col justify-center items-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">📚 本棚アプリ</h1>
          <p className="text-gray-600">あなたの読書ライフをサポート</p>
        </div>
        
        <div className="bg-white p-8 rounded-xl shadow-lg w-full max-w-md border border-gray-100">
          <h2 className="text-xl font-semibold mb-6 text-center text-gray-800">
            {isSignUp ? "✨ 新規アカウント登録" : "🔑 ログイン"}
          </h2>
          
          {authError && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              {authError}
            </div>
          )}
          
          <form onSubmit={isSignUp ? handleSignUp : handleEmailLogin} className="space-y-4">
            <div>
              <label className="block text-gray-700 mb-2 font-medium">📧 メールアドレス</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
            
            <div>
              <label className="block text-gray-700 mb-2 font-medium">🔒 パスワード</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
              />
            </div>
            
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-blue-500 to-blue-600 text-white py-3 px-4 rounded-lg hover:from-blue-600 hover:to-blue-700 transition-all duration-200 transform hover:scale-105 font-medium"
            >
              {isSignUp ? "🚀 登録する" : "✨ ログイン"}
            </button>
          </form>
          
          <button
            onClick={() => setIsSignUp(!isSignUp)}
            className="w-full text-blue-500 text-center hover:text-blue-600 mt-4 py-2 transition-colors"
          >
            {isSignUp ? "🔄 アカウントをお持ちの方はこちら" : "📝 新規登録はこちら"}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* ヘッダー - 2段構成に変更 */}
      <div className="bg-white shadow-sm border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4">
          {/* 1段目: タイトルとユーザー情報 */}
          <div className="flex items-center justify-between py-4 border-b border-gray-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center">
                <span className="text-white font-bold text-lg">📚</span>
              </div>
              <h1 className="text-2xl font-bold text-gray-800">本棚アプリ</h1>
            </div>
            
            <div className="flex items-center gap-3">
              <UserInfo />
              <button
                onClick={handleLogout}
                className="bg-red-500 text-white px-3 py-1.5 rounded-lg hover:bg-red-600 transition-colors text-sm"
              >
                ログアウト
              </button>
            </div>
          </div>

          {/* 2段目: 操作系ボタンと検索 */}
          <div className="py-4">
            <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
              {/* 左側: 並び替えと検索 */}
              <div className="flex flex-wrap gap-3">
                <div className="flex gap-2">
                  <SortButton
                    label="📅 作成順"
                    value="created_at"
                    current={sortBy}
                    onClick={(value) => setSortBy(value)}
                  />
                  <SortButton
                    label="⭐ 評価順"
                    value="rating"
                    current={sortBy}
                    onClick={(value) => setSortBy(value)}
                  />
                </div>

                <input
                  type="text"
                  placeholder="🔍 タイトル検索"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="border border-gray-200 px-3 py-2 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all min-w-0 w-64"
                />
              </div>

              {/* 右側: アクションボタン */}
              <div className="flex flex-wrap gap-2">
                <Link href="/add">
                  <button className="bg-green-500 text-white px-4 py-2 rounded-lg hover:bg-green-600 transition-all duration-200 transform hover:scale-105 shadow-sm">
                    ➕ 本を追加
                  </button>
                </Link>
                <Link href="/recommendations">
                  <button className="bg-purple-500 text-white px-4 py-2 rounded-lg hover:bg-purple-600 transition-all duration-200 transform hover:scale-105 shadow-sm">
                    📖 通常推薦
                  </button>
                </Link>
                <Link href="/ml-recommendations">
                  <button className="bg-gradient-to-r from-green-500 to-blue-500 text-white px-4 py-2 rounded-lg hover:from-green-600 hover:to-blue-600 transition-all duration-200 transform hover:scale-105 shadow-sm">
                    🤖 ML推薦
                  </button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* メインコンテンツ */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        {books.length === 0 ? (
          <div className="text-center py-16">
            <div className="text-6xl mb-4">📚</div>
            <h2 className="text-2xl font-semibold text-gray-700 mb-2">本棚が空です</h2>
            <p className="text-gray-500 mb-6">最初の一冊を追加してみましょう！</p>
            <Link href="/add">
              <button className="bg-gradient-to-r from-green-500 to-green-600 text-white px-6 py-3 rounded-lg hover:from-green-600 hover:to-green-700 transition-all duration-200 transform hover:scale-105 shadow-md">
                📖 本を追加する
              </button>
            </Link>
          </div>
        ) : (
          <ul className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
            {books
              .filter((book) =>
                book.title.toLowerCase().includes(searchTerm.toLowerCase())
              )
              .map((book) => (
                <BookCard key={book.id} book={book} onDelete={handleDelete} />
              ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// components/AuthButton.tsx
"use client";

import { supabase } from "../utils/supabaseClient"; 

export default function AuthButton() {
  const handleLogin = async () => {
    await supabase.auth.signInWithOAuth({ provider: "google" });
  };

  const handleLogout = async () => {
    await supabase.auth.signOut();
  };

  return (
    <div className="flex gap-4">
      <button onClick={handleLogin} className="bg-green-500 text-white px-4 py-2 rounded">
        Googleでログイン
      </button>
      <button onClick={handleLogout} className="bg-red-500 text-white px-4 py-2 rounded">
        ログアウト
      </button>
    </div>
  );
}

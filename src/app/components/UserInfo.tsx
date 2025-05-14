// app/components/UserInfo.tsx
"use client";

import { useEffect, useState } from "react";
import { supabase } from "../utils/supabaseClient";

type User = {
  id: string;
  email?: string;
};

export default function UserInfo() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    const fetchUser = async () => {
      const { data } = await supabase.auth.getUser();
      setUser(data.user);
    };
    fetchUser();
  }, []);

  if (!user) return <p className="text-gray-500">未ログイン</p>;

  return (
    <p className="text-blue-700 font-semibold">ログイン中：{user.email}</p>
  );
}

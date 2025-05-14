This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

### ローカルSupabaseのセットアップ

このプロジェクトはローカルでSupabaseを実行することを前提としています。以下の手順でセットアップしてください：

1. Supabase CLIをインストール
```bash
npm install -g supabase
```

2. Dockerがインストールされていることを確認してから、ローカルSupabaseを起動
```bash
supabase start
```

3. 環境変数ファイルの作成
プロジェクトのルートに`.env`ファイルを作成し、以下の内容を設定します：
```
# Supabase（ローカル）の接続情報
NEXT_PUBLIC_SUPABASE_URL=http://localhost:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0

# Prisma用のデータベース接続URL
DATABASE_URL=postgresql://postgres:postgres@localhost:54322/postgres
```

4. データベースのマイグレーション
```bash
npx prisma migrate dev
npx prisma generate
```

### 開発サーバーの起動

環境変数の設定とSupabaseの起動が完了したら、開発サーバーを起動します：

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## 認証について

このプロジェクトではメール＋パスワード認証を使用しています。ローカル環境では、メール確認のリンクがSupabase CLIの出力に表示されます。

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.

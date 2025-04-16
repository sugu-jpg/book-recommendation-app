import { supabase } from "@/app/utils/supabaseClient";
import { PrismaClient } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";

const prisma = new PrismaClient();

export async function GET(req: NextRequest) {
  try {
    const user_id = req.nextUrl.searchParams.get("user_id");

    if (!user_id) {
      return NextResponse.json(
        { message: "user_id が必要です" },
        { status: 400 }
      );
    }

    const books = await prisma.book.findMany({
      where: { user_id },
      orderBy: { created_at: "asc" },
    });

    return NextResponse.json({ message: "success", books }, { status: 200 });
  } catch (error) {
    return NextResponse.json({ message: "Error", error }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { title, description, image, rating, user_id } = body;

    if (!title || !user_id) {
      return NextResponse.json(
        { message: "タイトルとユーザーIDは必須です" },
        { status: 400 }
      );
    }

    const newBook = await prisma.book.create({
      data: {
        title,
        description,
        image,
        rating,
        user_id, // ← フロントから送られた値をそのまま使う
      },
    });

    return NextResponse.json(
      { message: "success", book: newBook },
      { status: 201 }
    );
  } catch (error) {
    return NextResponse.json({ message: "Error", error }, { status: 500 });
  } finally {
    await prisma.$disconnect();
  }
}

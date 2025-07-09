import { PrismaClient } from "@prisma/client";
import { NextRequest, NextResponse } from "next/server";

const prisma = new PrismaClient();

//１つの
export async function GET(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const id = parseInt(params.id);
  const book = await prisma.book.findUnique({
    where: { id },
  });

  if (!book) {
    return NextResponse.json({ message: "Not found" }, { status: 404 });
  }

  return NextResponse.json({ message: "success", book }, { status: 200 });
}

export async function DELETE(
  req: NextRequest,
  context: { params: { id: string } }
) {
  const id = parseInt(context.params.id);
  const book = await prisma.book.delete({
    where: { id },
  });

  return NextResponse.json(book);
}

export async function PUT(
  req: NextRequest,
  { params }: { params: { id: string } }
) {
  const id = parseInt(params.id);
  const { title, description, image, rating } = await req.json();
  const editBook = await prisma.book.update({
    data: { title, description, image, rating },
    where: { id },
  });

  return NextResponse.json({ message: "success", editBook }, { status: 200 });
}

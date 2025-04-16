// components/BookCard.tsx
import Link from "next/link";


type Props = {
  book: {
    id: number;
    title: string;
    description?: string;
    image?: string;
    rating?: number;
  };
  onDelete: (id: number) => void;
};

export default function BookCard({ book, onDelete }: Props) {
  return (
    <li className="bg-white p-4 rounded-xl shadow-md flex flex-col justify-between">
      <div>
        <h2 className="text-lg font-bold text-gray-800 mb-1">{book.title}</h2>
        <p className="text-sm text-gray-600 line-clamp-3">{book.description}</p>
        {book.rating !== undefined && (
          <p className="text-yellow-500 text-sm mt-1">
            {"★".repeat(book.rating) + "☆".repeat(5 - book.rating)}
          </p>
        )}
      </div>
      <img
        src={book.image || "https://via.placeholder.com/150"}
        alt={book.title}
        className="w-full h-48 object-cover rounded mt-3"
      />
      <div className="flex gap-2">
        <Link href={`/edit/${book.id}`} className="flex-1">
          <button className="w-full bg-blue-500 text-white py-2 rounded-lg hover:bg-blue-600 transition">
            編集
          </button>
        </Link>
        <button
          onClick={() => onDelete(book.id)}
          className="flex-1 bg-red-500 text-white py-2 rounded-lg hover:bg-red-600 transition"
        >
          削除
        </button>
      </div>
    </li>
  );
}

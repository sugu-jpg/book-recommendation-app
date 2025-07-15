// components/BookCard.tsx
import Link from "next/link";
import Image from "next/image";


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
    <li className="bg-white rounded-xl shadow-md hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1 border border-gray-100 overflow-hidden flex flex-col h-full">
      {book.image && (
        <div className="relative h-48 overflow-hidden flex-shrink-0">
          <Image
            src={book.image}
            alt={book.title}
            width={300}
            height={192}
            className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
          />
          <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent opacity-0 hover:opacity-100 transition-opacity duration-300"></div>
        </div>
      )}
      
      <div className="p-4 flex flex-col flex-grow">
        <h2 className="font-bold text-lg mb-2 text-gray-800 line-clamp-2">{book.title}</h2>
        
        <div className="flex-grow">
          {book.description && (
            <p className="text-gray-600 text-sm mb-3 line-clamp-3">
              {book.description}
            </p>
          )}
          
          {book.rating && (
            <div className="flex items-center mb-3">
              <span className="text-yellow-500 mr-1">⭐</span>
              <span className="text-sm text-gray-600">{book.rating}/5</span>
            </div>
          )}
        </div>
        
        {/* ボタンを下部に固定 */}
        <div className="flex gap-2 mt-auto">
          <Link href={`/edit/${book.id}`} className="flex-1">
            <button className="w-full bg-blue-500 text-white py-2 px-3 rounded-lg hover:bg-blue-600 transition-colors text-sm">
              ✏️ 編集
            </button>
          </Link>
          <button
            onClick={() => onDelete(book.id)}
            className="bg-red-500 text-white py-2 px-3 rounded-lg hover:bg-red-600 transition-colors text-sm"
          >
            🗑️
          </button>
        </div>
      </div>
    </li>
  );
}

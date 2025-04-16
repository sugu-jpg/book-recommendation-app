// app/components/SortButton.tsx
type Props = {
    label: string;
    value: "created_at" | "rating";
    current: "created_at" | "rating";
    onClick: (value: "created_at" | "rating") => void;
  };
  
  export default function SortButton({ label, value, current, onClick }: Props) {
    const isActive = value === current;
  
    return (
      <button
        onClick={() => onClick(value)}
        className={`px-4 py-2 rounded transition ${
          isActive
            ? "bg-blue-500 text-white hover:bg-blue-600"
            : "bg-gray-200 text-gray-800 hover:bg-gray-300"
        }`}
      >
        {label}
      </button>
    );
  }
  
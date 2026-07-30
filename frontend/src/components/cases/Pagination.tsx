type Props = {
  currentPage: number;
  totalPages: number;
  pageSize: number;
  totalItems: number;
  onPageChange: (page: number) => void;
};

export default function Pagination({
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
}: Props) {
  if (totalItems === 0) {
    return null;
  }

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  const pages = Array.from({ length: totalPages }, (_, index) => index + 1);

  return (
    <div className="flex justify-between items-center mt-5">
      <p className="text-sm text-gray-600">
        Showing {startItem} to {endItem} of {totalItems} cases
      </p>

      <div className="flex items-center gap-2">

        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 1}
          className="px-3 py-1 border rounded-lg disabled:opacity-50"
        >
          Previous
        </button>

        {pages.map((page) => (
          <button
            key={page}
            onClick={() => onPageChange(page)}
            className={`px-3 py-1 rounded-lg border ${
              currentPage === page
                ? "bg-orange-600 text-white border-orange-600"
                : "border-gray-300"
            }`}
          >
            {page}
          </button>
        ))}

        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages}
          className="px-3 py-1 border rounded-lg disabled:opacity-50"
        >
          Next
        </button>

      </div>
    </div>
  );
}
import { useEffect, useState } from "react";

export default function DocumentsList() {
  const [documents, setDocuments] = useState([]);

  useEffect(() => {
    fetch("http://localhost:8000/api/documents", {
      credentials: "include",
    })
      .then(res => res.json())
      .then(data => setDocuments(data))
      .catch(err => console.error("Failed to fetch documents:", err));
  }, []);

  if (documents.length === 0) {
    return <span className="text-sm text-gray-500 dark:text-gray-400">No documents yet</span>;
  }

  return (
    <nav className="flex flex-col gap-1 overflow-y-auto">
      {documents.map(doc => (
        <a
          key={doc.id}
          href="#"
          className="flex items-center gap-2 p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-800 transition-colors text-sm"
        >
          📄 {doc.name}
        </a>
      ))}
    </nav>
  );
}

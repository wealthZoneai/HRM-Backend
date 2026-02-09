import { FiChevronRight } from "react-icons/fi";
import { useNavigate } from "react-router-dom";

const Identification = () => {
  const navigate = useNavigate();

  const documents = [
    { label: "Aadhar Card *", key: "aadhar" },
    { label: "Pan Card *", key: "pan" },
    { label: "ID Card *", key: "idcard" },
    { label: "Visa", key: "visa" },
  ];

  return (
    <div className="space-y-4">
      {documents.map((doc) => (
        <button
          key={doc.key}
          onClick={() => navigate(`/upload/${doc.key}`)}
          className="w-full flex items-center justify-between border rounded-lg px-4 py-3 text-sm hover:bg-gray-50"
        >
          <span>{doc.label}</span>
          <FiChevronRight className="text-gray-500" />
        </button>
      ))}
    </div>
  );
};

export default Identification;

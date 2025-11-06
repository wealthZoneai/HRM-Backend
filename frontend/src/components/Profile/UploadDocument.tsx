import { useParams } from "react-router-dom";
import { FiCamera } from "react-icons/fi";

const UploadDocument = () => {
  const { type } = useParams();

  const titleMap: Record<string, string> = {
    aadhar: "Aadhar Card",
    pan: "Pan Card",
    idcard: "ID Card",
    visa: "Visa Document",
  };

  const title = titleMap[type || "aadhar"];

  return (
    <div className="max-w-md mx-auto p-6 space-y-6 bg-white rounded-xl">
      <h2 className="text-lg font-semibold">{title}</h2>
      <p className="text-sm text-gray-600">
        Upload focused photo of your {title} for faster verification
      </p>

      {/* Upload Box 1 */}
      <div className="border-2 border-dashed border-gray-300 rounded-xl p-5 text-center space-y-3">
        <p className="text-sm text-gray-600">
          Front side photo of your {title}
        </p>
        <button className="flex items-center justify-center gap-2 border border-blue-400 text-blue-500 rounded-full px-4 py-1 text-sm">
          <FiCamera className="text-lg" /> Upload Photo
        </button>
      </div>

      {/* Upload Box 2 */}
      <div className="border-2 border-dashed border-purple-400 rounded-xl p-5 text-center space-y-3">
        <p className="text-sm text-gray-600">
          Back side photo of your {title}
        </p>
        <button className="flex items-center justify-center gap-2 border border-blue-400 text-blue-500 rounded-full px-4 py-1 text-sm">
          <FiCamera className="text-lg" /> Upload Photo
        </button>
      </div>

      {/* Submit Button */}
      <button className="w-full bg-blue-500 text-white py-2 rounded-full hover:bg-blue-600 transition">
        Submit
      </button>
    </div>
  );
};

export default UploadDocument;

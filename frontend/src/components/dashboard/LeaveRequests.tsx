
export default function LeaveRequests() {
  const data = [
    { type: "Sick Leave", time: "2 hrs ago", status: "Pending" },
    { type: "Sick Leave", time: "13 days ago", status: "Approved" },
    { type: "Sick Leave", time: "2 days ago", status: "Rejected" },
  ];

  return (
    <div className="bg-white p-4 rounded-xl shadow w-full">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold">Leave Requests</h3>
        <button className="text-blue-600 text-sm">View All</button>
      </div>

      <div className="space-y-4">
        {data.map((req, i) => (
          <div
            key={i}
            className="flex justify-between items-center text-sm border p-2 rounded-lg"
          >
            <div>
              <p>You Applied For Leave</p>
              <p className="text-gray-500">Type: {req.type}</p>
            </div>
            <span
              className={`text-sm font-semibold px-3 py-1 rounded-lg ${
                req.status === "Pending"
                  ? "bg-yellow-100 text-yellow-600"
                  : req.status === "Approved"
                  ? "bg-green-100 text-green-600"
                  : "bg-red-100 text-red-600"
              }`}
            >
              {req.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

const ManagerFeedback = ({ feedback }: any) => {
  return (
    <div>
      <h3 className="font-semibold mb-3">Recent Feedback</h3>

      <div className="space-y-4">
        {feedback.map((item: any, index: number) => (
          <div
            key={index}
            className="border rounded-xl p-4 bg-white shadow-sm"
          >
            <p className="text-gray-500 text-sm mb-1">Manager Feedback</p>
            <p className="font-medium capitalize">{item.manager}</p>
            <p className="text-xs text-gray-400 mb-2">{item.date}</p>
            <p className="text-sm text-gray-700">{item.message}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ManagerFeedback;

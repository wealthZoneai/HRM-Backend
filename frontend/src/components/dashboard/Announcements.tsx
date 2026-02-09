export default function Announcements() {
  const data = [
    { day: "Mon", event: "Marketing Meeting", time: "10:00 AM" },
    { day: "Tue", event: "UI/UX Meeting", time: "11:00 AM" },
    { day: "Wed", event: "Full Stack Meeting", time: "12:30 AM" },
  ];

  return (
    <div className="bg-white p-4 rounded-xl shadow w-full">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold">Announcements</h3>
        <button className="text-blue-600 text-sm">View All</button>
      </div>

      <div className="space-y-3">
        {data.map((item, i) => (
          <div key={i} className="flex justify-between items-center text-sm">
            <span className="text-gray-500">{item.day}</span>
            <span className="font-medium">{item.event}</span>
            <span className="text-gray-500">{item.time}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function UpcomingHolidays() {
  const holidays = [
    { name: "New Year Day", date: "1st Jan, Monday" },
    { name: "Republic Day", date: "26th Jan, Friday" },
  ];

  return (
    <div className="bg-white p-4 rounded-xl shadow w-full">
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold">Upcoming Holidays</h3>
        <button className="text-blue-600 text-sm">View All</button>
      </div>

      <div className="space-y-3">
        {holidays.map((h, i) => (
          <div key={i} className="flex justify-between items-center text-sm">
            <span className="font-medium">{h.name}</span>
            <span className="text-gray-500">{h.date}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

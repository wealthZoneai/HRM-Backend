const CurrentObjectives = ({ objectives }: any) => (
  <div>
    <h3 className="font-semibold mb-3">Current Objectives</h3>
    {objectives.map((obj: any, i: number) => (
      <div key={i} className="border rounded-xl p-4 bg-white shadow-sm">
        <p className="font-medium">{obj.title}</p>
        <p className="text-sm text-gray-600 mb-3">{obj.description}</p>
        <div className="h-2 bg-gray-200 rounded">
          <div className="h-full bg-blue-500 rounded" style={{ width: `${obj.progress}%` }} />
        </div>
      </div>
    ))}
  </div>
);

export default CurrentObjectives;

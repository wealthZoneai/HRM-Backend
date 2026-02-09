const MetricsCard = ({ label, value, change }: any) => (
  <div className="border rounded-xl p-4 bg-white shadow-sm">
    <p className="text-gray-500 text-sm">{label}</p>
    <h3 className="text-xl font-semibold">{value}</h3>
    <p className="text-green-600 text-sm">{change}</p>
  </div>
);

export default MetricsCard;

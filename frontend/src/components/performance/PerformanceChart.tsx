import { BarChart, Bar, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";

const PerformanceChart = ({ data }: any) => (
  <div className="border rounded-xl p-6 bg-white">
    <h3 className="font-semibold mb-4">Performance Trend</h3>

    <BarChart width={360} height={200} data={data}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="day" />
      <YAxis />
      <Tooltip />
      <Bar dataKey="value" fill="#0057D9" />
    </BarChart>
  </div>
);

export default PerformanceChart;

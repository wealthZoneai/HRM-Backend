type Props = {
  label: string;
  time: string;
  actionLabel: string;
};

export default function TimeCard({ label, time, actionLabel }: Props) {
  return (
    <div className="bg-white p-4 rounded-xl shadow flex flex-col gap-2 w-full">
      <span className="text-sm text-gray-500">{label}</span>
      <h2 className="text-2xl font-semibold text-blue-600">{time}</h2>
      <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm w-fit">
        {actionLabel}
      </button>
    </div>
  );
}

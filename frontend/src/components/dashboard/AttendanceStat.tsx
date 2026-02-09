type StatProps = {
title: string;
value: number;
};


export default function AttendanceStat({ title, value }: StatProps) {
return (
<div className="bg-white p-4 rounded-xl shadow flex flex-col items-center w-full">
<span className="text-sm text-gray-600">{title}</span>
<h2 className="text-2xl font-bold">{value}</h2>
<div className="mt-2 w-12 h-12 rounded-full border-4 border-blue-600 flex items-center justify-center text-blue-600 font-semibold">
{value}%
</div>
</div>
);
}
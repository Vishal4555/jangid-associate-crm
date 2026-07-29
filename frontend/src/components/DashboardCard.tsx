type Props = {
  title: string;
  value: number;
};

export default function DashboardCard({
  title,
  value,
}: Props) {
  return (
    <div className="bg-white rounded-xl shadow p-6">
      <h3 className="text-gray-500">
        {title}
      </h3>

      <h1 className="text-3xl font-bold mt-2 text-emerald-700">
        {value.toLocaleString("en-IN")}
      </h1>
    </div>
  );
}
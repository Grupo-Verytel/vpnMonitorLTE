import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts';

import { ErrorAlert } from '@/components/common/ErrorAlert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatPercent } from '@/lib/format';
import { useSitesSummary } from '@/hooks/useSitesSummary';

const COLORS = {
  FIBRA: '#22c55e',
  LTE: '#eab308',
  DOWN: '#ef4444',
};

export function ChannelDistribution() {
  const { data, isLoading, isError, refetch } = useSitesSummary();

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Distribución actual</CardTitle>
        </CardHeader>
        <CardContent>
          <Skeleton className="mx-auto h-[260px] w-full max-w-sm" />
        </CardContent>
      </Card>
    );
  }

  if (isError || !data) {
    return <ErrorAlert onRetry={() => refetch()} />;
  }

  const chartData = [
    { name: 'Fibra', value: data.sites_fibra, pct: data.pct_fibra, color: COLORS.FIBRA },
    { name: 'LTE', value: data.sites_lte, pct: data.pct_lte, color: COLORS.LTE },
    { name: 'Caídos', value: data.sites_down, pct: data.pct_down, color: COLORS.DOWN },
  ].filter((d) => d.value > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Distribución actual</CardTitle>
        <p className="text-sm text-slate-600">Sitios por canal en este momento</p>
      </CardHeader>
      <CardContent>
        <div className="flex flex-col items-center gap-6 md:flex-row">
          <div className="relative h-[260px] w-full max-w-[260px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={chartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={70}
                  outerRadius={100}
                  paddingAngle={2}
                  dataKey="value"
                >
                  {chartData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  formatter={(value: number, name: string, item) => [
                    `${value} sitios (${formatPercent(item.payload.pct)})`,
                    name,
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-3xl font-semibold text-slate-900">{data.total_sites}</span>
              <span className="text-xs text-slate-500">total</span>
            </div>
          </div>

          <ul className="flex-1 space-y-3">
            {chartData.map((item) => (
              <li key={item.name} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <span
                    className="size-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="font-medium text-slate-700">{item.name}</span>
                </div>
                <span className="tabular-nums text-slate-600">
                  {item.value} ({formatPercent(item.pct)})
                </span>
              </li>
            ))}
          </ul>
        </div>
      </CardContent>
    </Card>
  );
}

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { ErrorAlert } from '@/components/common/ErrorAlert';
import { TimeRangeToggle } from '@/components/common/TimeRangeToggle';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate, formatTime } from '@/lib/format';
import { useLteTimeline } from '@/hooks/useLteTimeline';
import type { TimeRangeHours } from '@/types/api';

type Props = {
  hours: TimeRangeHours;
  onHoursChange: (hours: TimeRangeHours) => void;
};

export function LteTimelineChart({ hours, onHoursChange }: Props) {
  const { data, isLoading, isError, refetch } = useLteTimeline(hours);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div>
          <CardTitle className="text-lg">Uso LTE en el tiempo</CardTitle>
          <p className="text-sm text-muted-foreground">Porcentaje de sitios en canal LTE</p>
        </div>
        <TimeRangeToggle value={hours} onChange={onHoursChange} />
      </CardHeader>
      <CardContent>
        {isLoading && <Skeleton className="h-[300px] w-full" />}
        {isError && <ErrorAlert onRetry={() => refetch()} />}
        {data && !isError && (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart data={data.points} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="lteGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#eab308" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#eab308" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis
                dataKey="timestamp"
                tickFormatter={(v) => formatTime(v)}
                interval="preserveStartEnd"
                minTickGap={40}
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
              />
              <YAxis
                domain={[0, 100]}
                tickFormatter={(v) => `${v}%`}
                tick={{ fontSize: 12 }}
                className="fill-muted-foreground"
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null;
                  const point = payload[0].payload as (typeof data.points)[0];
                  return (
                    <div className="chart-tooltip">
                      <p className="font-medium">{formatDate(point.timestamp)}</p>
                      <p className="text-yellow-700 dark:text-yellow-400">LTE: {point.sites_lte} ({point.pct_lte.toFixed(1)}%)</p>
                      <p className="text-green-700 dark:text-green-400">Fibra: {point.sites_fibra}</p>
                      <p className="text-red-700 dark:text-red-400">Caídos: {point.sites_down}</p>
                    </div>
                  );
                }}
              />
              <Area
                type="monotone"
                dataKey="pct_lte"
                stroke="#ca8a04"
                strokeWidth={2}
                fill="url(#lteGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

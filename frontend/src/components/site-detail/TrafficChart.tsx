import { useMemo } from 'react';
import {
  Area,
  AreaChart,
  CartesianGrid,
  ReferenceArea,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { ErrorAlert } from '@/components/common/ErrorAlert';
import { TimeRangeToggle } from '@/components/common/TimeRangeToggle';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatBytes, formatDate, formatTime } from '@/lib/format';
import { useTrafficHistory } from '@/hooks/useTrafficHistory';
import type { TimeRangeHours } from '@/types/api';

type Props = {
  tunnelName: string;
  hours: TimeRangeHours;
  onHoursChange: (hours: TimeRangeHours) => void;
};

export function TrafficChart({ tunnelName, hours, onHoursChange }: Props) {
  const { data, isLoading, isError, refetch } = useTrafficHistory(tunnelName, hours);

  const lteBands = useMemo(() => {
    if (!data?.points.length) return [];
    const bands: { x1: string; x2: string }[] = [];
    let bandStart: string | null = null;

    data.points.forEach((point, i) => {
      const isLte = point.channel === 'LTE';
      if (isLte && !bandStart) bandStart = point.timestamp;
      if ((!isLte || i === data.points.length - 1) && bandStart) {
        const end = isLte && i === data.points.length - 1 ? point.timestamp : point.timestamp;
        bands.push({ x1: bandStart, x2: end });
        bandStart = null;
      }
    });
    return bands;
  }, [data]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-lg">Tráfico</CardTitle>
        <TimeRangeToggle value={hours} onChange={onHoursChange} />
      </CardHeader>
      <CardContent>
        {isLoading && <Skeleton className="h-[320px] w-full" />}
        {isError && <ErrorAlert onRetry={() => refetch()} />}
        {data && !isError && (
          <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={data.points} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="incoming" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.05} />
                </linearGradient>
                <linearGradient id="outgoing" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.05} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              {lteBands.map((band, i) => (
                <ReferenceArea
                  key={i}
                  x1={band.x1}
                  x2={band.x2}
                  fill="#fef08a"
                  fillOpacity={0.35}
                  strokeOpacity={0}
                />
              ))}
              <XAxis
                dataKey="timestamp"
                tickFormatter={(v) => formatTime(v)}
                tick={{ fontSize: 12, fill: '#64748b' }}
                minTickGap={40}
              />
              <YAxis
                tickFormatter={(v) => formatBytes(v)}
                tick={{ fontSize: 12, fill: '#64748b' }}
                width={70}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (!active || !payload?.[0]) return null;
                  const point = payload[0].payload as (typeof data.points)[0];
                  return (
                    <div className="rounded-lg border border-slate-200 bg-white p-3 text-sm shadow-md">
                      <p className="font-medium">{formatDate(point.timestamp)}</p>
                      <p className="text-blue-600">Entrada: {formatBytes(point.incoming_bytes)}</p>
                      <p className="text-cyan-600">Salida: {formatBytes(point.outgoing_bytes)}</p>
                      <p className="text-slate-600">Canal: {point.channel}</p>
                    </div>
                  );
                }}
              />
              <Area
                type="monotone"
                dataKey="incoming_bytes"
                name="Entrada"
                stackId="1"
                stroke="#3b82f6"
                fill="url(#incoming)"
              />
              <Area
                type="monotone"
                dataKey="outgoing_bytes"
                name="Salida"
                stackId="1"
                stroke="#06b6d4"
                fill="url(#outgoing)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

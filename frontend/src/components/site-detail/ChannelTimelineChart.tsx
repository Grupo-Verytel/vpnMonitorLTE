import { useMemo, useState } from 'react';

import { ChannelBadge } from '@/components/common/ChannelBadge';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { TimeRangeToggle } from '@/components/common/TimeRangeToggle';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { formatDate, formatTime } from '@/lib/format';
import { cn } from '@/lib/utils';
import { useChannelTimeline } from '@/hooks/useChannelTimeline';
import type { ChannelType, TimeRangeHours } from '@/types/api';

const CHANNEL_COLORS: Record<ChannelType, string> = {
  FIBRA: 'bg-green-500',
  LTE: 'bg-yellow-500',
  DOWN: 'bg-red-500',
  UNKNOWN: 'bg-slate-400',
};

type Props = {
  tunnelName: string;
  hours: TimeRangeHours;
  onHoursChange: (hours: TimeRangeHours) => void;
};

export function ChannelTimelineChart({ tunnelName, hours, onHoursChange }: Props) {
  const { data, isLoading, isError, refetch } = useChannelTimeline(tunnelName, hours);
  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);

  const buckets = data?.buckets ?? [];

  const timeLabels = useMemo(() => {
    if (buckets.length === 0) return [];
    const step = Math.max(1, Math.floor(buckets.length / 8));
    return buckets
      .filter((_, i) => i % step === 0 || i === buckets.length - 1)
      .map((b) => ({ label: formatTime(b.bucket_start), index: buckets.indexOf(b) }));
  }, [buckets]);

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <div>
          <CardTitle className="text-lg">Timeline de canal</CardTitle>
          <p className="text-sm text-muted-foreground">Buckets de 15 minutos</p>
        </div>
        <TimeRangeToggle value={hours} onChange={onHoursChange} />
      </CardHeader>
      <CardContent>
        {isLoading && <Skeleton className="h-[100px] w-full" />}
        {isError && <ErrorAlert onRetry={() => refetch()} />}
        {data && !isError && buckets.length > 0 && (
          <>
            <div className="flex h-10 w-full overflow-hidden rounded-md border border-border">
              {buckets.map((bucket, index) => (
                <div
                  key={`${bucket.bucket_start}-${index}`}
                  className={cn(
                    'h-full flex-1 cursor-pointer transition-opacity hover:opacity-80',
                    CHANNEL_COLORS[bucket.channel],
                    index === hoveredIndex && 'ring-2 ring-slate-400 ring-inset',
                  )}
                  onMouseEnter={() => setHoveredIndex(index)}
                  onMouseLeave={() => setHoveredIndex(null)}
                  title={`${formatTime(bucket.bucket_start)} – ${bucket.channel}`}
                />
              ))}
            </div>

            <div className="mt-2 flex justify-between text-xs text-muted-foreground">
              {timeLabels.map((t) => (
                <span key={t.index}>{t.label}</span>
              ))}
            </div>

            {hoveredIndex != null && buckets[hoveredIndex] && (
              <div className="mt-4 rounded-lg border border-border bg-muted/50 p-3 text-sm">
                <p className="font-medium">
                  {formatTime(buckets[hoveredIndex].bucket_start)} –{' '}
                  {formatTime(buckets[hoveredIndex].bucket_end)}
                </p>
                <p className="text-muted-foreground">{formatDate(buckets[hoveredIndex].bucket_start)}</p>
                <div className="mt-2">
                  <ChannelBadge channel={buckets[hoveredIndex].channel} size="sm" />
                </div>
              </div>
            )}

            <div className="mt-4 flex flex-wrap gap-4 text-xs text-muted-foreground">
              <span className="flex items-center gap-1.5">
                <span className="size-3 rounded-sm bg-green-500" /> Fibra
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-3 rounded-sm bg-yellow-500" /> LTE
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-3 rounded-sm bg-red-500" /> Caído
              </span>
              <span className="flex items-center gap-1.5">
                <span className="size-3 rounded-sm bg-slate-400" /> Sin datos
              </span>
            </div>
          </>
        )}
        {data && !isError && buckets.length === 0 && (
          <p className="text-sm text-muted-foreground">Sin datos de timeline en este período.</p>
        )}
      </CardContent>
    </Card>
  );
}

import { ArrowDown, ArrowUp, Minus } from 'lucide-react';

import { ChannelBadge } from '@/components/common/ChannelBadge';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDuration, formatTime } from '@/lib/format';
import { useSiteEvents } from '@/hooks/useSiteEvents';
import type { ChannelType, TimeRangeHours } from '@/types/api';

type Props = {
  tunnelName: string;
  hours: TimeRangeHours;
};

const channelRank: Record<ChannelType, number> = {
  FIBRA: 3,
  LTE: 2,
  UNKNOWN: 1,
  DOWN: 0,
};

function getTrend(from: ChannelType, to: ChannelType): 'up' | 'down' | 'neutral' {
  const diff = channelRank[to] - channelRank[from];
  if (diff > 0) return 'up';
  if (diff < 0) return 'down';
  return 'neutral';
}

export function SiteEventsTable({ tunnelName, hours }: Props) {
  const { data, isLoading, isError, refetch } = useSiteEvents(tunnelName, hours);

  if (isLoading) {
    return <div className="h-48 animate-pulse rounded-lg bg-muted" />;
  }

  if (isError) {
    return <ErrorAlert onRetry={() => refetch()} />;
  }

  if (!data?.events.length) {
    return <EmptyState title="Sin eventos de cambio de canal en este período" />;
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Hora</TableHead>
          <TableHead>Cambio</TableHead>
          <TableHead>Duración anterior</TableHead>
          <TableHead className="w-12" />
        </TableRow>
      </TableHeader>
      <TableBody>
        {data.events.map((event, i) => {
          const trend = getTrend(event.from_channel, event.to_channel);
          return (
            <TableRow key={`${event.timestamp}-${i}`}>
              <TableCell className="font-mono text-sm">{formatTime(event.timestamp)}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <ChannelBadge channel={event.from_channel} size="sm" />
                  <span className="text-muted-foreground">→</span>
                  <ChannelBadge channel={event.to_channel} size="sm" />
                </div>
              </TableCell>
              <TableCell className="text-muted-foreground">
                {event.duration_minutes != null
                  ? formatDuration(event.duration_minutes)
                  : '—'}
              </TableCell>
              <TableCell>
                {trend === 'up' && <ArrowUp className="size-4 text-green-500" />}
                {trend === 'down' && <ArrowDown className="size-4 text-red-500" />}
                {trend === 'neutral' && <Minus className="size-4 text-muted-foreground" />}
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

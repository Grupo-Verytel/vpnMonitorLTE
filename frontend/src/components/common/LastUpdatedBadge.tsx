import { useEffect, useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { es } from 'date-fns/locale';
import { RefreshCw } from 'lucide-react';

import { cn } from '@/lib/utils';

type Props = {
  lastUpdated?: Date;
  isFetching?: boolean;
  className?: string;
};

function getFreshnessColor(lastUpdated?: Date): string {
  if (!lastUpdated) return 'text-slate-500';
  const seconds = (Date.now() - lastUpdated.getTime()) / 1000;
  if (seconds < 60) return 'text-green-600';
  if (seconds < 300) return 'text-yellow-600';
  return 'text-red-600';
}

export function LastUpdatedBadge({ lastUpdated, isFetching, className }: Props) {
  const [, setTick] = useState(0);

  useEffect(() => {
    const id = setInterval(() => setTick((t) => t + 1), 5000);
    return () => clearInterval(id);
  }, []);

  const label = lastUpdated
    ? `Actualizado ${formatDistanceToNow(lastUpdated, { addSuffix: true, locale: es })}`
    : 'Sin actualizar';

  return (
    <div
      className={cn(
        'flex items-center gap-2 text-sm',
        getFreshnessColor(lastUpdated),
        className,
      )}
    >
      <RefreshCw className={cn('size-4', isFetching && 'animate-spin')} />
      <span>{label}</span>
    </div>
  );
}

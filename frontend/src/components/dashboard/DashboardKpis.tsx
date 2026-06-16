import { AlertTriangle, Cable, Radio, Server } from 'lucide-react';

import { ErrorAlert } from '@/components/common/ErrorAlert';
import { KpiCard } from '@/components/common/KpiCard';
import { Skeleton } from '@/components/ui/skeleton';
import { formatPercent } from '@/lib/format';
import { useSitesSummary } from '@/hooks/useSitesSummary';

export function DashboardKpis() {
  const { data, isLoading, isError, refetch } = useSitesSummary();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-32 rounded-lg" />
        ))}
      </div>
    );
  }

  if (isError || !data) {
    return <ErrorAlert onRetry={() => refetch()} />;
  }

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
      <KpiCard
        label="Total sitios"
        value={data.total_sites}
        icon={Server}
        color="gray"
      />
      <KpiCard
        label="En Fibra"
        value={data.sites_fibra}
        subtitle={formatPercent(data.pct_fibra)}
        icon={Cable}
        color="green"
      />
      <KpiCard
        label="En LTE"
        value={data.sites_lte}
        subtitle={formatPercent(data.pct_lte)}
        icon={Radio}
        color="yellow"
      />
      <KpiCard
        label="Caídos"
        value={data.sites_down}
        subtitle={formatPercent(data.pct_down)}
        icon={AlertTriangle}
        color="red"
      />
    </div>
  );
}

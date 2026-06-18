import { KpiCard } from '@/components/common/KpiCard';
import { formatDuration } from '@/lib/format';
import type { SitePeriodStats } from '@/types/api';
import { Activity, Cable, Clock, Radio } from 'lucide-react';

/** Oculto temporalmente — reactivar cuando haga falta. */
const SHOW_DOWN_AND_CHANNEL_STATS = false;

type Props = {
  title: string;
  stats: SitePeriodStats;
};

export function SiteStatsGroup({ title, stats }: Props) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-muted-foreground">{title}</h3>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <KpiCard
          label="Tiempo en LTE"
          value={formatDuration(stats.lte_minutes)}
          icon={Radio}
          color="yellow"
        />
        <KpiCard
          label="Tiempo en Fibra"
          value={formatDuration(stats.fibra_minutes)}
          icon={Cable}
          color="green"
        />
        {SHOW_DOWN_AND_CHANNEL_STATS && (
          <>
            <KpiCard
              label="Tiempo caído"
              value={formatDuration(stats.down_minutes)}
              icon={Clock}
              color="red"
            />
            <KpiCard
              label="Cambios de canal"
              value={stats.channel_changes}
              icon={Activity}
              color="gray"
            />
          </>
        )}
      </div>
    </div>
  );
}

type SiteStatsCardProps = {
  statsToday: SitePeriodStats;
  statsWeek: SitePeriodStats;
};

export function SiteStatsCard({ statsToday, statsWeek }: SiteStatsCardProps) {
  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
      <SiteStatsGroup title="Hoy" stats={statsToday} />
      <SiteStatsGroup title="Últimos 7 días" stats={statsWeek} />
    </div>
  );
}

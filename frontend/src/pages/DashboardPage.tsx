import { useTimeRange } from '@/components/common/TimeRangeToggle';
import { ChannelDistribution } from '@/components/dashboard/ChannelDistribution';
import { DashboardKpis } from '@/components/dashboard/DashboardKpis';
import { LteRankingTable } from '@/components/dashboard/LteRankingTable';
import { LteTimelineChart } from '@/components/dashboard/LteTimelineChart';

export default function DashboardPage() {
  const { hours, setHours } = useTimeRange(24);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-600">
          Vista general del estado de los sitios remotos VPN
        </p>
      </div>

      <DashboardKpis />

      <LteTimelineChart hours={hours} onHoursChange={setHours} />

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        <ChannelDistribution />
        <LteRankingTable />
      </div>
    </div>
  );
}

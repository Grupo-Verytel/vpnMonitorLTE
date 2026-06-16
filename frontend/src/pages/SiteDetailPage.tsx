import { useParams } from 'react-router-dom';

import { useTimeRange } from '@/components/common/TimeRangeToggle';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { ChannelTimelineChart } from '@/components/site-detail/ChannelTimelineChart';
import { SiteCurrentStatusCard } from '@/components/site-detail/SiteCurrentStatusCard';
import { SiteEventsTable } from '@/components/site-detail/SiteEventsTable';
import { SiteHeader } from '@/components/site-detail/SiteHeader';
import { SiteInfoCard } from '@/components/site-detail/SiteInfoCard';
import { SiteStatsCard } from '@/components/site-detail/SiteStatsCard';
import { TrafficChart } from '@/components/site-detail/TrafficChart';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useSiteDetail } from '@/hooks/useSiteDetail';

export default function SiteDetailPage() {
  const { tunnelName = '' } = useParams();
  const decodedName = decodeURIComponent(tunnelName);
  const { data, isLoading, isError, refetch, isFetching } = useSiteDetail(decodedName);
  const { hours, setHours } = useTimeRange(24);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-10 w-64" />
        <Skeleton className="h-40 w-full" />
        <Skeleton className="h-32 w-full" />
        <Skeleton className="h-80 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return <ErrorAlert title="Sitio no encontrado" onRetry={() => refetch()} />;
  }

  return (
    <div className="space-y-6">
      <SiteHeader site={data} onRefresh={() => refetch()} isRefreshing={isFetching} />

      <SiteInfoCard site={data} />
      <SiteCurrentStatusCard site={data} />
      <SiteStatsCard statsToday={data.stats_today} statsWeek={data.stats_week} />

      <Tabs defaultValue="traffic">
        <TabsList>
          <TabsTrigger value="traffic">Tráfico (24h)</TabsTrigger>
          <TabsTrigger value="timeline">Timeline de canal</TabsTrigger>
          <TabsTrigger value="events">Eventos</TabsTrigger>
        </TabsList>

        <TabsContent value="traffic" className="mt-4">
          <TrafficChart
            tunnelName={decodedName}
            hours={hours}
            onHoursChange={setHours}
          />
        </TabsContent>

        <TabsContent value="timeline" className="mt-4">
          <ChannelTimelineChart
            tunnelName={decodedName}
            hours={hours}
            onHoursChange={setHours}
          />
        </TabsContent>

        <TabsContent value="events" className="mt-4">
          <SiteEventsTable tunnelName={decodedName} hours={hours} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { ChannelEventsResponse, TimeRangeHours } from '@/types/api';

export function useSiteEvents(tunnelName: string, hours: TimeRangeHours = 24) {
  return useQuery({
    queryKey: ['sites', 'events', tunnelName, hours],
    queryFn: async () => {
      const { data } = await api.get<ChannelEventsResponse>(
        `/api/sites/${encodeURIComponent(tunnelName)}/events`,
        { params: { hours } },
      );
      return data;
    },
    enabled: Boolean(tunnelName),
  });
}

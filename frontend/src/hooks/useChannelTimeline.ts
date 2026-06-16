import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { ChannelTimelineResponse, TimeRangeHours } from '@/types/api';

export function useChannelTimeline(tunnelName: string, hours: TimeRangeHours = 24) {
  return useQuery({
    queryKey: ['sites', 'channel-timeline', tunnelName, hours],
    queryFn: async () => {
      const { data } = await api.get<ChannelTimelineResponse>(
        `/api/sites/${encodeURIComponent(tunnelName)}/channel-timeline`,
        { params: { hours } },
      );
      return data;
    },
    enabled: Boolean(tunnelName),
  });
}

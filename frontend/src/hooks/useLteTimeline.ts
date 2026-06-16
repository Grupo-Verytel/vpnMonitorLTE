import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { LteUsageTimelineResponse, TimeRangeHours } from '@/types/api';

export function useLteTimeline(hours: TimeRangeHours = 24) {
  return useQuery({
    queryKey: ['sites', 'lte-timeline', hours],
    queryFn: async () => {
      const { data } = await api.get<LteUsageTimelineResponse>(
        '/api/sites/lte-usage-timeline',
        { params: { hours } },
      );
      return data;
    },
  });
}

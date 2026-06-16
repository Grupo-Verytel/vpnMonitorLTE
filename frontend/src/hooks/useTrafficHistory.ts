import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { TrafficHistoryResponse, TimeRangeHours } from '@/types/api';

export function useTrafficHistory(tunnelName: string, hours: TimeRangeHours = 24) {
  return useQuery({
    queryKey: ['sites', 'traffic-history', tunnelName, hours],
    queryFn: async () => {
      const { data } = await api.get<TrafficHistoryResponse>(
        `/api/sites/${encodeURIComponent(tunnelName)}/traffic-history`,
        { params: { hours } },
      );
      return data;
    },
    enabled: Boolean(tunnelName),
  });
}

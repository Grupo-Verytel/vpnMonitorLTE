import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { SiteDetail } from '@/types/api';

export function useSiteDetail(tunnelName: string) {
  return useQuery({
    queryKey: ['sites', 'detail', tunnelName],
    queryFn: async () => {
      const { data } = await api.get<SiteDetail>(
        `/api/sites/${encodeURIComponent(tunnelName)}`,
      );
      return data;
    },
    enabled: Boolean(tunnelName),
  });
}

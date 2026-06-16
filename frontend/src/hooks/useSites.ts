import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { SiteListResponse, SitesFilters } from '@/types/api';

export function useSites(filters: SitesFilters = {}) {
  return useQuery({
    queryKey: ['sites', 'list', filters],
    queryFn: async () => {
      const { data } = await api.get<SiteListResponse>('/api/sites', {
        params: {
          channel: filters.channel || undefined,
          locality: filters.locality || undefined,
          search: filters.search || undefined,
        },
      });
      return data;
    },
  });
}

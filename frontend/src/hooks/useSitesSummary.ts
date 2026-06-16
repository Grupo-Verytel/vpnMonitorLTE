import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { SitesSummary } from '@/types/api';

export function useSitesSummary() {
  return useQuery({
    queryKey: ['sites', 'summary'],
    queryFn: async () => {
      const { data } = await api.get<SitesSummary>('/api/sites/summary');
      return data;
    },
  });
}

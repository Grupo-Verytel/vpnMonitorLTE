import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { LocalitiesResponse } from '@/types/api';

export function useLocalities() {
  return useQuery({
    queryKey: ['sites', 'localities'],
    queryFn: async () => {
      const { data } = await api.get<LocalitiesResponse>('/api/sites/localities');
      return data;
    },
  });
}

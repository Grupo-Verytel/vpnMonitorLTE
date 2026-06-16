import { useQuery } from '@tanstack/react-query';

import { api } from '@/lib/api';
import type { LteRankingResponse } from '@/types/api';

type Options = {
  days?: number;
  limit?: number;
};

export function useLteRanking({ days = 7, limit = 10 }: Options = {}) {
  return useQuery({
    queryKey: ['sites', 'lte-ranking', days, limit],
    queryFn: async () => {
      const { data } = await api.get<LteRankingResponse>('/api/sites/lte-ranking', {
        params: { days, limit },
      });
      return data;
    },
  });
}

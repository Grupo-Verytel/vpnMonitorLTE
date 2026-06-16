import { QueryClient } from '@tanstack/react-query';

export const REFETCH_INTERVAL =
  Number(import.meta.env.VITE_REFETCH_INTERVAL_MS) || 30000;

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchInterval: REFETCH_INTERVAL,
      refetchOnWindowFocus: true,
      retry: 2,
      staleTime: 10_000,
    },
  },
});

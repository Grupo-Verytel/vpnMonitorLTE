import { useEffect, useState } from 'react';

import { SitesFilters } from '@/components/sites/SitesFilters';
import { SitesTable } from '@/components/sites/SitesTable';
import { useSites } from '@/hooks/useSites';
import type { SitesFilters as SitesFiltersType } from '@/types/api';

function useDebounce<T>(value: T, delay: number): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(id);
  }, [value, delay]);
  return debounced;
}

export default function SitesPage() {
  const [filters, setFilters] = useState<SitesFiltersType>({});
  const debouncedSearch = useDebounce(filters.search, 300);

  const queryFilters: SitesFiltersType = {
    channel: filters.channel,
    locality: filters.locality,
    search: debouncedSearch,
  };

  const { data } = useSites(queryFilters);

  return (
    <div className="space-y-2">
      <div>
        <h1 className="text-2xl font-semibold text-slate-900">Sitios</h1>
        <p className="text-sm text-slate-600">
          Lista de sitios remotos con canal actual y métricas de tráfico
        </p>
      </div>

      <SitesFilters
        filters={filters}
        onChange={setFilters}
        showing={data?.items.length ?? 0}
        total={data?.total ?? 0}
      />

      <SitesTable filters={queryFilters} />
    </div>
  );
}

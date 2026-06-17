import { Search, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import type { SitesFilters } from '@/types/api';

type Props = {
  filters: SitesFilters;
  onChange: (filters: SitesFilters) => void;
  showing: number;
  total: number;
};

export function SitesFilters({ filters, onChange, showing, total }: Props) {
  const clearFilters = () => onChange({});

  const hasFilters = Boolean(filters.search || filters.channel);

  return (
    <div className="sticky top-0 z-20 -mx-6 mb-6 border-b border-border bg-background/95 px-6 py-4 backdrop-blur">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar por nombre o túnel..."
            className="pl-9"
            value={filters.search ?? ''}
            onChange={(e) => onChange({ ...filters, search: e.target.value || undefined })}
          />
        </div>

        <Select
          value={filters.channel ?? 'all'}
          onValueChange={(v) =>
            onChange({ ...filters, channel: v === 'all' ? undefined : v })
          }
        >
          <SelectTrigger className="w-full lg:w-[160px]">
            <SelectValue placeholder="Canal" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">Todos los canales</SelectItem>
            <SelectItem value="FIBRA">Fibra</SelectItem>
            <SelectItem value="LTE">LTE</SelectItem>
            <SelectItem value="DOWN">Caído</SelectItem>
          </SelectContent>
        </Select>

        {hasFilters && (
          <Button variant="outline" onClick={clearFilters} className="shrink-0">
            <X className="size-4" />
            Limpiar filtros
          </Button>
        )}

        <p className="text-sm text-muted-foreground lg:ml-auto lg:whitespace-nowrap">
          Mostrando <span className="font-medium text-foreground">{showing}</span> de{' '}
          <span className="font-medium text-foreground">{total}</span> sitios
        </p>
      </div>
    </div>
  );
}

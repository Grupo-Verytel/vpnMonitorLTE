import { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  flexRender,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  useReactTable,
  type ColumnDef,
  type SortingState,
} from '@tanstack/react-table';
import { ArrowUpDown, ChevronLeft, ChevronRight } from 'lucide-react';

import { ChannelBadge } from '@/components/common/ChannelBadge';
import { EmptyState } from '@/components/common/EmptyState';
import { ErrorAlert } from '@/components/common/ErrorAlert';
import { Button } from '@/components/ui/button';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatBytes, formatBytesPerMin, formatDuration, formatRelative } from '@/lib/format';
import { cn } from '@/lib/utils';
import { useSites } from '@/hooks/useSites';
import type { SiteListItem, SitesFilters } from '@/types/api';

import { SitesTableSkeleton } from './SitesTableSkeleton';

const PAGE_SIZE = 25;

const rowBorderClass: Record<string, string> = {
  FIBRA: 'border-l-green-500',
  LTE: 'border-l-yellow-500 bg-yellow-50/30 dark:bg-yellow-950/20',
  DOWN: 'border-l-red-500 bg-red-50/30 dark:bg-red-950/20',
  UNKNOWN: 'border-l-slate-300 dark:border-l-slate-600',
};

type Props = {
  filters: SitesFilters;
};

export function SitesTable({ filters }: Props) {
  const navigate = useNavigate();
  const [sorting, setSorting] = useState<SortingState>([]);
  const { data, isLoading, isError, refetch } = useSites(filters);

  const columns = useMemo<ColumnDef<SiteListItem>[]>(
    () => [
      {
        accessorKey: 'site_name',
        header: ({ column }) => (
          <Button
            variant="ghost"
            size="sm"
            className="-ml-3 h-8"
            onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
          >
            Sitio
            <ArrowUpDown className="ml-1 size-3.5" />
          </Button>
        ),
        cell: ({ row }) => (
          <div>
            <div className="font-medium">{row.original.site_name ?? row.original.tunnel_name}</div>
            <div className="text-xs text-muted-foreground">{row.original.tunnel_name}</div>
          </div>
        ),
      },
      {
        accessorKey: 'channel',
        header: 'Canal',
        cell: ({ row }) => <ChannelBadge channel={row.original.channel} />,
      },
      {
        accessorKey: 'traffic_last_5m_bytes',
        header: 'Tráfico (5m)',
        cell: ({ row }) => formatBytes(row.original.traffic_last_5m_bytes),
      },
      {
        accessorKey: 'traffic_bytes_per_min',
        header: 'Bytes/min (15m)',
        cell: ({ row }) => formatBytesPerMin(row.original.traffic_bytes_per_min),
      },
      {
        accessorKey: 'last_lte_at',
        header: 'Última vez en LTE',
        cell: ({ row }) =>
          row.original.last_lte_at ? formatRelative(row.original.last_lte_at) : '—',
      },
      {
        accessorKey: 'lte_minutes_today',
        header: 'LTE hoy',
        cell: ({ row }) => formatDuration(row.original.lte_minutes_today),
      },
      {
        id: 'actions',
        header: '',
        cell: ({ row }) => (
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/sites/${encodeURIComponent(row.original.tunnel_name)}`)}
          >
            Ver detalle
          </Button>
        ),
      },
    ],
    [navigate],
  );

  const table = useReactTable({
    data: data?.items ?? [],
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    initialState: { pagination: { pageSize: PAGE_SIZE } },
  });

  if (isLoading) return <SitesTableSkeleton />;
  if (isError) return <ErrorAlert onRetry={() => refetch()} />;
  if (!data || data.items.length === 0) {
    return (
      <EmptyState title="No se encontraron sitios con esos filtros" />
    );
  }

  return (
    <div className="space-y-4">
      <div className="overflow-x-auto rounded-lg border border-border bg-card">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((hg) => (
              <TableRow key={hg.id}>
                {hg.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder
                      ? null
                      : flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow
                key={row.id}
                className={cn(
                  'border-l-[3px] hover:bg-muted/50',
                  rowBorderClass[row.original.channel],
                )}
              >
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {table.getPageCount() > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-muted-foreground">
            Página {table.getState().pagination.pageIndex + 1} de {table.getPageCount()}
          </p>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.previousPage()}
              disabled={!table.getCanPreviousPage()}
            >
              <ChevronLeft className="size-4" />
              Anterior
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => table.nextPage()}
              disabled={!table.getCanNextPage()}
            >
              Siguiente
              <ChevronRight className="size-4" />
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}

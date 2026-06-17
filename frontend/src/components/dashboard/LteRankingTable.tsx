import { ErrorAlert } from '@/components/common/ErrorAlert';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { formatDuration, formatPercent } from '@/lib/format';
import { useLteRanking } from '@/hooks/useLteRanking';

export function LteRankingTable() {
  const { data, isLoading, isError, refetch } = useLteRanking({ days: 7, limit: 10 });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Top sitios en LTE</CardTitle>
        <p className="text-sm text-muted-foreground">Últimos 7 días — mayor tiempo en canal de respaldo</p>
      </CardHeader>
      <CardContent>
        {isLoading && (
          <div className="space-y-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        )}
        {isError && <ErrorAlert onRetry={() => refetch()} />}
        {data && !isError && (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-12">#</TableHead>
                <TableHead>Sitio</TableHead>
                <TableHead className="text-right">Minutos LTE</TableHead>
                <TableHead className="text-right">% del tiempo</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.items.map((item, index) => {
                const pct =
                  item.total_minutes > 0
                    ? (item.lte_minutes / item.total_minutes) * 100
                    : 0;
                return (
                  <TableRow key={item.tunnel_name}>
                    <TableCell className="font-medium text-muted-foreground">{index + 1}</TableCell>
                    <TableCell>
                      <div className="font-medium">{item.site_name ?? item.tunnel_name}</div>
                      <div className="text-xs text-muted-foreground">{item.tunnel_name}</div>
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatDuration(item.lte_minutes)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums text-yellow-700 dark:text-yellow-400">
                      {formatPercent(pct)}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}

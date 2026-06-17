import { ArrowLeft, RefreshCw } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

import { Button } from '@/components/ui/button';
import type { SiteDetail } from '@/types/api';

type Props = {
  site: SiteDetail;
  onRefresh: () => void;
  isRefreshing?: boolean;
};

export function SiteHeader({ site, onRefresh, isRefreshing }: Props) {
  const navigate = useNavigate();
  const name = site.catalog?.site_name ?? site.tunnel_name;

  return (
    <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3">
        <Button variant="outline" size="sm" onClick={() => navigate('/sites')}>
          <ArrowLeft className="size-4" />
          Volver
        </Button>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">{name}</h1>
          <p className="text-sm text-muted-foreground">{site.tunnel_name}</p>
        </div>
      </div>
      <Button variant="outline" size="sm" onClick={onRefresh} disabled={isRefreshing}>
        <RefreshCw className={isRefreshing ? 'animate-spin' : ''} />
        Actualizar
      </Button>
    </div>
  );
}

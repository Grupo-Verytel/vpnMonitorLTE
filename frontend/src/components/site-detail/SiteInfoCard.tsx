import { MapPin, User } from 'lucide-react';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { SiteDetail } from '@/types/api';

type Props = {
  site: SiteDetail;
};

export function SiteInfoCard({ site }: Props) {
  const catalog = site.catalog;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">Información general</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 sm:grid-cols-2">
        <div>
          <p className="text-2xl font-semibold text-slate-900">
            {catalog?.site_name ?? site.tunnel_name}
          </p>
          <p className="mt-1 font-mono text-sm text-slate-500">{site.tunnel_name}</p>
        </div>
        <div className="space-y-2 text-sm text-slate-600">
          {catalog?.site_address && (
            <p className="flex items-start gap-2">
              <MapPin className="mt-0.5 size-4 shrink-0" />
              {catalog.site_address}
            </p>
          )}
          <p>
            <span className="font-medium text-slate-700">Localidad:</span>{' '}
            {catalog?.locality ?? 'Sin asignar'}
          </p>
          <p>
            <span className="font-medium text-slate-700">Proyecto:</span>{' '}
            {catalog?.project_code ?? '—'}
          </p>
          {catalog?.contact_person && (
            <p className="flex items-center gap-2">
              <User className="size-4" />
              {catalog.contact_person}
            </p>
          )}
          <p>
            <span className="font-medium text-slate-700">Gateway remoto:</span>{' '}
            {site.current.remote_gateway ?? '—'}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

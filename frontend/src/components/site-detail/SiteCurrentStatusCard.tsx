import { AlertTriangle } from 'lucide-react';

import { ChannelBadge } from '@/components/common/ChannelBadge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Card, CardContent } from '@/components/ui/card';
import { formatBytesPerMin } from '@/lib/format';
import type { SiteDetail } from '@/types/api';

type Props = {
  site: SiteDetail;
};

const channelMessages = {
  LTE: 'Este sitio está usando **LTE**',
  FIBRA: 'Este sitio está usando **Fibra**',
  DOWN: 'Este sitio está **sin conexión**',
  UNKNOWN: 'Estado del canal **desconocido**',
};

export function SiteCurrentStatusCard({ site }: Props) {
  const { channel } = site.current;
  const message = channelMessages[channel];

  return (
    <Card className="border-2 border-slate-200">
      <CardContent className="flex flex-col gap-6 p-6 md:flex-row md:items-center md:justify-between">
        <div className="space-y-4">
          <ChannelBadge channel={channel} size="lg" />
          <p
            className="text-lg text-slate-700"
            dangerouslySetInnerHTML={{
              __html: message.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'),
            }}
          />
          {channel === 'LTE' && (
            <Alert className="border-yellow-300 bg-yellow-50">
              <AlertTriangle className="size-4 text-yellow-600" />
              <AlertDescription className="text-yellow-800">
                El sitio está consumiendo el canal de respaldo
              </AlertDescription>
            </Alert>
          )}
        </div>
        <div className="space-y-2 text-sm md:text-right">
          <p className="text-slate-600">
            Tráfico (15m):{' '}
            <span className="font-semibold text-slate-900">
              {formatBytesPerMin(site.current.traffic_bytes_per_min)}
            </span>
          </p>
          <p className="text-slate-600">
            Estado:{' '}
            <span className="font-medium capitalize text-slate-900">
              {site.current.status}
            </span>
          </p>
        </div>
      </CardContent>
    </Card>
  );
}

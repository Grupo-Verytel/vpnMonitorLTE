import { AlertCircle } from 'lucide-react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';

type Props = {
  title?: string;
  message?: string;
  onRetry?: () => void;
};

export function ErrorAlert({
  title = 'Error al cargar',
  message = 'No se pudieron obtener los datos. Intenta de nuevo.',
  onRetry,
}: Props) {
  return (
    <Alert variant="destructive" className="border-red-200 bg-red-50 dark:border-red-900 dark:bg-red-950/50">
      <AlertCircle className="size-4 text-red-600 dark:text-red-400" />
      <AlertTitle className="text-red-800 dark:text-red-300">{title}</AlertTitle>
      <AlertDescription className="text-red-700 dark:text-red-400">
        <p>{message}</p>
        {onRetry && (
          <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
            Reintentar
          </Button>
        )}
      </AlertDescription>
    </Alert>
  );
}

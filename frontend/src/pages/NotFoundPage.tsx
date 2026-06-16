import { Link } from 'react-router-dom';
import { Home } from 'lucide-react';

import { Button } from '@/components/ui/button';

export default function NotFoundPage() {
  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center text-center">
      <p className="text-6xl font-bold text-slate-200">404</p>
      <h1 className="mt-4 text-2xl font-semibold text-slate-900">Página no encontrada</h1>
      <p className="mt-2 text-sm text-slate-600">
        La ruta que buscas no existe en este monitor.
      </p>
      <Button asChild className="mt-6">
        <Link to="/">
          <Home className="size-4" />
          Ir al Dashboard
        </Link>
      </Button>
    </div>
  );
}

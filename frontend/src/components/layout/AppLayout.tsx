import { useEffect, useMemo, useState } from 'react';
import { Outlet, useLocation, useParams } from 'react-router-dom';
import { useIsFetching, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { cn } from '@/lib/utils';
import { useSiteDetail } from '@/hooks/useSiteDetail';

export function AppLayout() {
  const location = useLocation();
  const { tunnelName } = useParams();
  const queryClient = useQueryClient();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [offline, setOffline] = useState(false);

  const { data: siteDetail } = useSiteDetail(tunnelName ?? '');

  useEffect(() => {
    const mqTablet = window.matchMedia('(max-width: 1023px)');
    const mqMobile = window.matchMedia('(max-width: 767px)');

    const update = () => {
      setSidebarCollapsed(mqTablet.matches);
      if (!mqMobile.matches) setMobileOpen(false);
    };

    update();
    mqTablet.addEventListener('change', update);
    mqMobile.addEventListener('change', update);
    return () => {
      mqTablet.removeEventListener('change', update);
      mqMobile.removeEventListener('change', update);
    };
  }, []);

  useEffect(() => {
    const check = () => {
      const state = queryClient.getQueryState(['sites', 'summary']);
      setOffline(Boolean(state?.error && axios.isAxiosError(state.error) && !state.error.response));
    };
    check();
    const unsub = queryClient.getQueryCache().subscribe(check);
    return () => unsub();
  }, [queryClient]);

  const breadcrumbs = useMemo(() => {
    if (location.pathname === '/') return [{ label: 'Dashboard' }];
    if (location.pathname === '/sites') return [{ label: 'Sitios' }];
    if (location.pathname.startsWith('/sites/') && tunnelName) {
      return [
        { label: 'Sitios', href: '/sites' },
        { label: siteDetail?.catalog?.site_name ?? tunnelName },
      ];
    }
    return [{ label: 'Página no encontrada' }];
  }, [location.pathname, tunnelName, siteDetail]);

  const isFetching = useIsFetching();

  const lastUpdated = useMemo(() => {
    const queries = queryClient.getQueryCache().findAll({ type: 'active' });
    const timestamps = queries
      .map((q) => q.state.dataUpdatedAt)
      .filter((t) => t > 0);
    if (timestamps.length === 0) return undefined;
    return new Date(Math.max(...timestamps));
  }, [queryClient, isFetching]);

  return (
    <div className="min-h-screen bg-slate-50">
      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileOpen}
        onMobileClose={() => setMobileOpen(false)}
        onMobileToggle={() => setMobileOpen(true)}
      />

      <div
        className={cn(
          'flex min-h-screen flex-col transition-all duration-200',
          sidebarCollapsed ? 'md:pl-[72px]' : 'md:pl-60',
        )}
      >
        {offline && (
          <div className="bg-red-600 px-4 py-2 text-center text-sm font-medium text-white">
            ⚠️ Sin conexión con el servidor
          </div>
        )}

        <Header
          breadcrumbs={breadcrumbs}
          lastUpdated={lastUpdated}
          sidebarCollapsed={sidebarCollapsed}
        />

        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

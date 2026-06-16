import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Menu, Radio, Shield, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

type Props = {
  collapsed: boolean;
  mobileOpen: boolean;
  onMobileClose: () => void;
  onMobileToggle: () => void;
};

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/sites', label: 'Sitios', icon: Radio, end: false },
];

export function Sidebar({ collapsed, mobileOpen, onMobileClose, onMobileToggle }: Props) {
  const appName = import.meta.env.VITE_APP_NAME || 'FortiGate VPN Monitor';

  return (
    <>
      {mobileOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/40 lg:hidden"
          onClick={onMobileClose}
          aria-hidden
        />
      )}

      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 flex flex-col border-r border-slate-200 bg-white transition-all duration-200',
          collapsed ? 'w-[72px]' : 'w-60',
          mobileOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0',
        )}
      >
        <div className="flex h-[60px] items-center gap-2 border-b border-slate-200 px-4">
          <Shield className="size-6 shrink-0 text-slate-800" />
          {!collapsed && (
            <span className="text-sm font-semibold leading-tight text-slate-900">{appName}</span>
          )}
          <Button
            variant="ghost"
            size="icon"
            className="ml-auto md:hidden"
            onClick={onMobileClose}
            aria-label="Cerrar menú"
          >
            <X className="size-5" />
          </Button>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {navItems.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              onClick={onMobileClose}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-slate-100 text-slate-900'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900',
                  collapsed && 'justify-center px-2',
                )
              }
              title={collapsed ? label : undefined}
            >
              <Icon className="size-5 shrink-0" />
              {!collapsed && <span>{label}</span>}
            </NavLink>
          ))}
        </nav>
      </aside>

      <Button
        variant="outline"
        size="icon"
        className="fixed bottom-4 left-4 z-30 md:hidden"
        onClick={onMobileToggle}
        aria-label="Abrir menú"
      >
        <Menu className="size-5" />
      </Button>
    </>
  );
}

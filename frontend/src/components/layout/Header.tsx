import { useIsFetching } from '@tanstack/react-query';
import { Link, useLocation } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';

import { LastUpdatedBadge } from '@/components/common/LastUpdatedBadge';
import { ThemeToggle } from '@/components/common/ThemeToggle';
import { cn } from '@/lib/utils';

type Breadcrumb = { label: string; href?: string };

type Props = {
  breadcrumbs: Breadcrumb[];
  lastUpdated?: Date;
  sidebarCollapsed: boolean;
};

export function Header({ breadcrumbs, lastUpdated, sidebarCollapsed }: Props) {
  const location = useLocation();
  const isFetching = useIsFetching() > 0;

  return (
    <header
      className={cn(
        'sticky top-0 z-30 flex h-[60px] items-center justify-between border-b border-border bg-card/95 px-6 backdrop-blur',
        sidebarCollapsed ? 'md:pl-[88px]' : 'md:pl-[264px]',
      )}
    >
      <nav className="flex items-center gap-1 text-sm text-muted-foreground" aria-label="Breadcrumb">
        {breadcrumbs.map((crumb, i) => (
          <span key={`${crumb.label}-${i}`} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="size-4 text-muted-foreground/60" />}
            {crumb.href ? (
              <Link to={crumb.href} className="hover:text-foreground">
                {crumb.label}
              </Link>
            ) : (
              <span className="font-medium text-foreground">{crumb.label}</span>
            )}
          </span>
        ))}
        {breadcrumbs.length === 0 && (
          <span className="font-medium text-foreground">
            {location.pathname === '/' ? 'Dashboard' : 'FortiGate VPN Monitor'}
          </span>
        )}
      </nav>

      <div className="flex items-center gap-4">
        <ThemeToggle />
        <LastUpdatedBadge
          lastUpdated={lastUpdated}
          isFetching={isFetching}
        />
      </div>
    </header>
  );
}

import type { LucideIcon } from 'lucide-react';
import { Inbox } from 'lucide-react';

import { cn } from '@/lib/utils';

type Props = {
  title: string;
  description?: string;
  icon?: LucideIcon;
  className?: string;
};

export function EmptyState({
  title,
  description,
  icon: Icon = Inbox,
  className,
}: Props) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center rounded-lg border border-dashed border-border bg-card py-12 text-center',
        className,
      )}
    >
      <Icon className="mb-3 size-10 text-muted-foreground/40" />
      <p className="text-sm font-medium text-foreground">{title}</p>
      {description && <p className="mt-1 text-sm text-muted-foreground">{description}</p>}
    </div>
  );
}

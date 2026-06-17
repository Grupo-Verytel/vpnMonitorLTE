import type { LucideIcon } from 'lucide-react';
import { TrendingDown, TrendingUp } from 'lucide-react';

import { cn } from '@/lib/utils';

type Props = {
  label: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: 'up' | 'down' | 'neutral';
  color?: 'gray' | 'green' | 'yellow' | 'red' | 'blue';
};

const colorMap = {
  gray: {
    icon: 'bg-slate-100 text-slate-600 dark:bg-slate-800 dark:text-slate-300',
    value: 'text-foreground',
  },
  green: {
    icon: 'bg-green-100 text-green-600 dark:bg-green-950 dark:text-green-400',
    value: 'text-green-700 dark:text-green-400',
  },
  yellow: {
    icon: 'bg-yellow-100 text-yellow-600 dark:bg-yellow-950 dark:text-yellow-400',
    value: 'text-yellow-700 dark:text-yellow-400',
  },
  red: {
    icon: 'bg-red-100 text-red-600 dark:bg-red-950 dark:text-red-400',
    value: 'text-red-700 dark:text-red-400',
  },
  blue: {
    icon: 'bg-blue-100 text-blue-600 dark:bg-blue-950 dark:text-blue-400',
    value: 'text-blue-700 dark:text-blue-400',
  },
};

export function KpiCard({
  label,
  value,
  subtitle,
  icon: Icon,
  trend,
  color = 'gray',
}: Props) {
  const colors = colorMap[color];

  return (
    <div className="rounded-lg border border-border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">{label}</p>
          <p
            className={cn(
              'text-3xl font-semibold tabular-nums transition-all duration-300',
              colors.value,
            )}
          >
            {value}
          </p>
          {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
        </div>
        <div className="flex flex-col items-end gap-2">
          <div className={cn('rounded-lg p-2.5', colors.icon)}>
            <Icon className="size-5" />
          </div>
          {trend === 'up' && <TrendingUp className="size-4 text-green-500" />}
          {trend === 'down' && <TrendingDown className="size-4 text-red-500" />}
        </div>
      </div>
    </div>
  );
}

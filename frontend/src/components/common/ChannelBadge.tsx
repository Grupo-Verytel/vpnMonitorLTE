import { AlertTriangle, Cable, HelpCircle, Radio } from 'lucide-react';

import { cn } from '@/lib/utils';
import type { ChannelType } from '@/types/api';

type Props = {
  channel: ChannelType;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
};

const config: Record<
  ChannelType,
  { label: string; icon: typeof Radio; classes: string }
> = {
  LTE: {
    label: 'LTE',
    icon: Radio,
    classes:
      'bg-yellow-100 text-yellow-800 border-yellow-300 dark:bg-yellow-950 dark:text-yellow-300 dark:border-yellow-800',
  },
  FIBRA: {
    label: 'Fibra',
    icon: Cable,
    classes:
      'bg-green-100 text-green-800 border-green-300 dark:bg-green-950 dark:text-green-300 dark:border-green-800',
  },
  DOWN: {
    label: 'Caído',
    icon: AlertTriangle,
    classes:
      'bg-red-100 text-red-800 border-red-300 dark:bg-red-950 dark:text-red-300 dark:border-red-800',
  },
  UNKNOWN: {
    label: 'Sin datos',
    icon: HelpCircle,
    classes:
      'bg-gray-100 text-gray-600 border-gray-300 dark:bg-gray-800 dark:text-gray-300 dark:border-gray-600',
  },
};

const sizeClasses = {
  sm: 'text-xs px-2 py-0.5 gap-1 [&_svg]:size-3',
  md: 'text-xs px-2.5 py-0.5 gap-1.5 [&_svg]:size-3.5',
  lg: 'text-base px-4 py-2 gap-2 [&_svg]:size-5',
};

export function ChannelBadge({ channel, size = 'md', className }: Props) {
  const { label, icon: Icon, classes } = config[channel];

  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border font-medium',
        classes,
        sizeClasses[size],
        className,
      )}
    >
      <Icon />
      {label}
    </span>
  );
}

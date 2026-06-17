import { useState } from 'react';
import { cn } from '@/lib/utils';
import type { TimeRangeHours } from '@/types/api';

import { Button } from '@/components/ui/button';

type Option = { label: string; value: TimeRangeHours };

const OPTIONS: Option[] = [
  { label: '6h', value: 6 },
  { label: '24h', value: 24 },
  { label: '7d', value: 168 },
];

type Props = {
  value: TimeRangeHours;
  onChange: (value: TimeRangeHours) => void;
  className?: string;
};

export function TimeRangeToggle({ value, onChange, className }: Props) {
  return (
    <div className={cn('inline-flex rounded-md border border-border bg-card p-0.5', className)}>
      {OPTIONS.map((opt) => (
        <Button
          key={opt.value}
          type="button"
          variant={value === opt.value ? 'secondary' : 'ghost'}
          size="sm"
          className={cn('h-8 px-3', value === opt.value && 'shadow-sm')}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </Button>
      ))}
    </div>
  );
}

export function useTimeRange(defaultValue: TimeRangeHours = 24) {
  const [hours, setHours] = useState<TimeRangeHours>(defaultValue);
  return { hours, setHours };
}

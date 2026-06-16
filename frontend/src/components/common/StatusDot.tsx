import { cn } from '@/lib/utils';
import type { ChannelType } from '@/types/api';

type Props = {
  channel: ChannelType;
  className?: string;
};

const colors: Record<ChannelType, string> = {
  FIBRA: 'bg-green-500',
  LTE: 'bg-yellow-500',
  DOWN: 'bg-red-500',
  UNKNOWN: 'bg-gray-400',
};

export function StatusDot({ channel, className }: Props) {
  return (
    <span
      className={cn('inline-block size-2 rounded-full', colors[channel], className)}
      aria-hidden
    />
  );
}

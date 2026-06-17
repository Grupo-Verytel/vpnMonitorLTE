import { Loader2 } from 'lucide-react';

import { cn } from '@/lib/utils';

type Props = {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
};

const sizes = { sm: 'size-4', md: 'size-6', lg: 'size-8' };

export function LoadingSpinner({ className, size = 'md' }: Props) {
  return (
    <Loader2 className={cn('animate-spin text-muted-foreground', sizes[size], className)} />
  );
}

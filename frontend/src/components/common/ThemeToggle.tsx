import { Moon, Sun } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useTheme } from '@/contexts/ThemeContext';
import { cn } from '@/lib/utils';

type Props = {
  className?: string;
};

export function ThemeToggle({ className }: Props) {
  const { theme, setTheme } = useTheme();

  return (
    <div
      className={cn(
        'inline-flex rounded-md border border-border bg-card p-0.5',
        className,
      )}
      role="group"
      aria-label="Seleccionar tema"
    >
      <Button
        type="button"
        variant={theme === 'light' ? 'secondary' : 'ghost'}
        size="sm"
        className="h-8 gap-1.5 px-2.5"
        onClick={() => setTheme('light')}
        aria-pressed={theme === 'light'}
        aria-label="Modo claro"
      >
        <Sun className="size-4" />
        <span className="hidden sm:inline">Claro</span>
      </Button>
      <Button
        type="button"
        variant={theme === 'dark' ? 'secondary' : 'ghost'}
        size="sm"
        className="h-8 gap-1.5 px-2.5"
        onClick={() => setTheme('dark')}
        aria-pressed={theme === 'dark'}
        aria-label="Modo oscuro"
      >
        <Moon className="size-4" />
        <span className="hidden sm:inline">Oscuro</span>
      </Button>
    </div>
  );
}

# FortiGate VPN Monitor — Frontend

Webapp React para visualizar qué sitios remotos VPN están usando el canal LTE (respaldo) versus Fibra (principal), con datos en tiempo casi real desde el backend FastAPI.

## Stack

- React 18 + Vite + TypeScript (strict)
- TanStack Query v5 — cache y refetch automático cada 30s
- TanStack Table v8 — tabla de sitios con ordenamiento y paginación
- React Router v6 — navegación
- Tailwind CSS v3 + shadcn/ui — componentes UI
- Recharts — gráficas de timeline, distribución y tráfico
- Lucide React — iconografía
- date-fns (locale `es`) — fechas relativas y formateo
- Axios — cliente HTTP
- Sonner — notificaciones toast

## Setup local

```bash
cd frontend
npm install   # o pnpm install
cp .env.example .env
# Editar VITE_API_BASE_URL (ej. http://localhost:8000)
npm run dev
```

La app corre en [http://localhost:5173](http://localhost:5173).

### Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `VITE_API_BASE_URL` | URL base del backend FastAPI | `http://localhost:8000` |
| `VITE_REFETCH_INTERVAL_MS` | Intervalo de refetch en ms | `30000` |
| `VITE_APP_NAME` | Nombre en sidebar | `FortiGate VPN Monitor` |

## Deploy en Vercel

1. Conectar el repositorio en [vercel.com](https://vercel.com).
2. Configurar **Root Directory** como `frontend`.
3. Framework preset: **Vite**.
4. Agregar variable de entorno:
   - `VITE_API_BASE_URL` = `https://fortigate-vpn-monitor-backend.up.railway.app` (o tu URL de Railway)
5. Deploy. El archivo `vercel.json` incluye rewrites SPA.

## Estructura de carpetas

```
src/
├── components/
│   ├── ui/           # shadcn (Button, Card, Table, etc.)
│   ├── layout/       # AppLayout, Sidebar, Header
│   ├── common/       # ChannelBadge, KpiCard, etc.
│   ├── dashboard/    # KPIs, gráficas, ranking LTE
│   ├── sites/        # Tabla y filtros de sitios
│   └── site-detail/  # Detalle, tráfico, eventos
├── hooks/            # TanStack Query hooks por endpoint
├── lib/              # api, format, utils, query-client
├── pages/            # Dashboard, Sitios, Detalle, 404
├── routes/           # Definición de rutas
└── types/            # Tipos TypeScript del API
```

## Cómo agregar una pantalla nueva

1. Crear página en `src/pages/MiPagina.tsx` (default export).
2. Si necesita datos, crear hook en `src/hooks/useMiRecurso.ts` con TanStack Query.
3. Agregar tipos en `src/types/api.ts` si aplica.
4. Registrar ruta en `src/routes/index.tsx`.
5. Agregar item de navegación en `src/components/layout/Sidebar.tsx`.

## Pantallas

### Dashboard (`/`)

- 4 KPI cards: total sitios, Fibra, LTE, Caídos
- Gráfica de área: % sitios en LTE (6h / 24h / 7d)
- Donut: distribución actual por canal
- Tabla top 10 sitios con más tiempo en LTE (7 días)

### Sitios (`/sites`)

- Filtros: búsqueda (debounce 300ms), canal, localidad
- Tabla TanStack con borde de color por canal
- Paginación de 25 filas

### Detalle (`/sites/:tunnelName`)

- Info del sitio, estado actual con alerta LTE
- Estadísticas hoy y últimos 7 días
- Tabs: Tráfico, Timeline de canal, Eventos

## Capturas (conceptuales)

> Placeholders — reemplazar con capturas reales tras el primer deploy.

| Pantalla | Descripción |
|---|---|
| Dashboard | Grid de KPIs semáforo + gráfica amarilla de LTE + donut verde/amarillo/rojo |
| Sitios | Tabla densa con filtros sticky y filas con borde izquierdo de color |
| Detalle | Card de estado grande + tabs con gráficas de tráfico apilado |

## Scripts

```bash
npm run dev      # desarrollo
npm run build    # build producción
npm run preview  # preview del build
```

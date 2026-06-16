# FortiGate VPN Monitor — Backend

Backend en **FastAPI + Python 3.11** para monitorear túneles IPsec de un FortiGate 70G. Toma snapshots periódicos vía REST API del FortiGate, persiste métricas en MySQL y expone endpoints REST para un frontend React.

## Stack

| Componente | Tecnología |
|---|---|
| Framework | FastAPI |
| Runtime | Python 3.11 |
| ORM | SQLAlchemy 2.x |
| Migraciones | Alembic |
| Base de datos | MySQL 8 en AWS RDS (PyMySQL) |
| Scheduler | APScheduler (BackgroundScheduler) |
| HTTP Client | httpx |
| Config | pydantic-settings |
| Logging | structlog (JSON) |
| Deploy | Railway (Docker) |

## Variables de entorno

| Variable | Descripción | Default |
|---|---|---|
| `FORTIGATE_HOST` | IP o hostname del FortiGate | — |
| `FORTIGATE_TOKEN` | Token REST API (Bearer) | — |
| `FORTIGATE_VERIFY_SSL` | Verificar certificado SSL | `false` |
| `FORTIGATE_TIMEOUT_SECONDS` | Timeout HTTP al FortiGate | `15` |
| `DATABASE_URL` | URL SQLAlchemy hacia RDS MySQL | — |
| `DATABASE_SSL_CA` | Ruta al CA bundle de AWS RDS (SSL) | vacío |
| `SCHEDULER_ENABLED` | Activar scheduler embebido | `true` |
| `SCHEDULER_INTERVAL_MINUTES` | Intervalo entre snapshots | `1` |
| `INTERNAL_CRON_TOKEN` | Token para endpoints `/internal/*` | — |
| `CORS_ORIGINS` | Orígenes CORS (comma-separated) | `http://localhost:5173` |
| `LOG_LEVEL` | Nivel de log | `INFO` |
| `LOG_JSON` | Salida JSON estructurada | `true` |
| `TZ` | Timezone del proceso | `America/Bogota` |
| `SNAPSHOT_RETENTION_DAYS` | Días de retención de snapshots | `60` |

## Setup local

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Editar .env con tus credenciales

# Crear la base de datos en RDS (o local) y aplicar migraciones
alembic upgrade head

# Iniciar servidor de desarrollo
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Tests

```bash
pytest -v
```

## Base de datos — AWS RDS MySQL

La aplicación se conecta a **MySQL 8 en RDS** mediante `DATABASE_URL`. No uses el plugin MySQL de Railway; el backend en Railway apunta a tu instancia RDS externa.

### Formato de `DATABASE_URL`

```
mysql+pymysql://usuario:contraseña@tu-instancia.xxxxx.region.rds.amazonaws.com:3306/fortigate_monitor?charset=utf8mb4
```

Si la contraseña tiene caracteres especiales (`@`, `#`, `%`, etc.), codifícala:

```python
from urllib.parse import quote
quote("mi@pass#123", safe="")  # → mi%40pass%23123
```

### Preparar RDS

1. Crear instancia **MySQL 8** en RDS (ej. `db.t4g.micro` para empezar).
2. Crear la base de datos `fortigate_monitor` y un usuario con permisos `CREATE`, `SELECT`, `INSERT`, `UPDATE`, `DELETE`.
3. En el **Security Group** de RDS, permitir entrada **TCP 3306** desde:
   - Tu IP (desarrollo local), y/o
   - El rango de IPs de salida de Railway (o habilitar acceso público con SG restrictivo).
4. Anotar el **endpoint** de RDS (hostname sin puerto).

### SSL (recomendado en producción)

Descarga el [CA bundle de AWS RDS](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/UsingWithRDS.SSL.html) y configura:

```env
DATABASE_SSL_CA=/path/to/global-bundle.pem
```

En Railway, puedes incluir el cert en la imagen Docker o montarlo como variable/archivo según tu setup.

### Migraciones contra RDS

Desde tu máquina local (con acceso al RDS):

```bash
# .env apuntando al endpoint RDS
alembic upgrade head
```

O desde Railway tras el deploy:

```bash
railway run alembic upgrade head
```

## Deploy en Railway

1. **Conectar repositorio** en [Railway](https://railway.app) apuntando a la carpeta `backend/`.
2. **Configurar `DATABASE_URL`** con el endpoint de tu RDS MySQL (no agregar plugin MySQL de Railway).
3. **Configurar variables de entorno** (críticas):
   - `DATABASE_URL` — endpoint RDS (ver sección anterior)
   - `DATABASE_SSL_CA` — opcional, ruta al CA bundle en el contenedor
   - `FORTIGATE_HOST`
   - `FORTIGATE_TOKEN`
   - `FORTIGATE_VERIFY_SSL=false` (o `true` con cert importado)
   - `INTERNAL_CRON_TOKEN` (generar un valor seguro)
   - `CORS_ORIGINS` (URL del frontend)
   - `SCHEDULER_ENABLED=true`
   - `TZ=America/Bogota`
4. **Migraciones**: ejecutar una vez tras el primer deploy (si no las corriste antes desde local):
   ```bash
   railway run alembic upgrade head
   ```
5. **Verificar**: `GET https://tu-app.railway.app/health` — el campo `db_connected` debe ser `true`.

## Endpoints

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/` | Info del servicio |
| GET | `/health` | Healthcheck (Railway) |
| GET | `/api/tunnels/current` | Último snapshot completo |
| GET | `/api/tunnels/active?minutes=5` | Túneles con tráfico activo |
| GET | `/api/tunnels/{name}/history?hours=24` | Serie temporal |
| GET | `/api/tunnels/{name}/detail` | Estado actual + catálogo |
| GET | `/api/metrics/summary` | KPIs del último snapshot |
| GET | `/api/metrics/top-consumers?limit=10&minutes=5` | Top consumidores |
| GET | `/api/metrics/status-changes?hours=24` | Cambios up↔down |
| POST | `/internal/trigger-snapshot` | Snapshot manual (token) |
| POST | `/internal/cleanup` | Cleanup manual (token) |

Los endpoints `/internal/*` requieren header `X-Internal-Token`.

## Consideraciones operativas

### Por qué `--workers 1`

APScheduler corre **dentro del mismo proceso** que uvicorn. Si se levantan múltiples workers, cada uno iniciaría su propio scheduler y se tomarían snapshots duplicados. El `Dockerfile`, `Procfile` y `railway.toml` fuerzan `--workers 1`.

### SSL self-signed del FortiGate

Por defecto `FORTIGATE_VERIFY_SSL=false`. En producción, importa el certificado CA del FortiGate:

```bash
# Exportar cert del FortiGate y configurar
export SSL_CERT_FILE=/path/to/fortigate-ca.pem
# FORTIGATE_VERIFY_SSL=true
```

### Regenerar token REST del FortiGate

1. Acceder al FortiGate vía CLI o GUI.
2. `execute api-user generate-key <usuario_api>`
3. Actualizar `FORTIGATE_TOKEN` en Railway.

### Estrategia de cleanup

- Job automático diario a las **3:00 AM** hora Colombia.
- Borra headers con `snapshot_time` anterior a `SNAPSHOT_RETENTION_DAYS`.
- Los detalles se eliminan en cascada (FK `ON DELETE CASCADE`).
- Cleanup manual: `POST /internal/cleanup` con `X-Internal-Token`.

### Agregar entradas al catálogo de túneles

Insertar directamente en `vpn_tunnels_catalog`:

```sql
INSERT INTO vpn_tunnels_catalog (tunnel_name, site_name, site_address, locality, project_code, contact_person, notes)
VALUES ('nombre-tunel-fortigate', 'Sede Principal', 'Calle 123', 'Bogotá', 'PRJ-001', 'Juan Pérez', 'Notas');
```

El `tunnel_name` debe coincidir exactamente con el nombre del túnel en FortiGate.

## Arquitectura

```
FortiGate REST API ──► FortiGateClient (httpx)
                            │
                            ▼
                    SnapshotService ──► RDS MySQL
                            ▲
                    APScheduler (cada N min)
                            │
                     FastAPI REST API ──► Frontend React
```

## Licencia

Uso interno del proyecto VPN Monitor.

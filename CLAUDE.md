# InsightFlow

## Qué es
Proyecto de portfolio: plataforma de analítica para una empresa B2B SaaS ficticia.
Datos sintéticos realistas → BigQuery → dbt en capas → API en FastAPI → frontend
web en Next.js con dashboard y un agente de IA que responde preguntas de negocio
en lenguaje natural.

El objetivo del proyecto es mostrar un sistema completo, prolijo y bien diseñado,
y servir de base de aprendizaje para el estilo de frontend que después se va a
reutilizar en demos para pymes.

## Estado de la reforma
- [x] Fase 1: datos sintéticos estáticos con historia y dbt reorganizado
- [x] Fase 2: API en FastAPI (métricas y agente)
- [ ] Fase 3: frontend en Next.js
- [ ] Fase 4: despliegue (API en Cloud Run, frontend en Vercel)

La app anterior en Streamlit (`agent/`) se mantiene funcionando hasta que el nuevo
frontend la reemplace, y después se elimina.

## Estado de los datos (Fase 1)
- **Dataset publicado:** semilla 42, ventana 2024-09 a 2026-08. Para reproducirlo
  hay que pasar `--end-month 2026-08`: sin ese flag el generador termina en el
  último mes completo y los números de `docs/data-stories.md` cambian.
- **Marts nuevos** (los únicos que usan la API y el agente): `kpi_summary`,
  `fct_mrr_monthly`, `fct_mrr_movements`, `fct_churn`, `fct_retention_cohorts`,
  `fct_unit_economics`, `dim_organizations`, `dim_plans`. Sus descripciones están en
  `dbt_insightflow/models/marts/schema.yml` y son el contexto del agente.
- **Tablas heredadas en `dbt_marts`** (`fact_*`, `kpi_active_companies`,
  `kpi_churn_rate`, `kpi_mrr_growth`): congeladas, solo para la app Streamlit.
  dbt ya no las gestiona; se borran junto con `agent/`.
- **Credenciales:** tanto el generador como dbt usan Application Default
  Credentials (`gcloud auth application-default login`).

## Decisiones tomadas
- **Sin ejecución programada.** Se elimina la generación diaria (GitHub Actions
  programado y Prefect). Los datos se generan una sola vez con un comando
  determinístico (semilla fija) y se cargan con full refresh.
- **Idioma:** código, datos, modelos y UI en inglés (portfolio internacional).
  Documentación del repo en inglés; los prompts y la conversación pueden ser en
  español.
- **Almacenamiento:** Google BigQuery (región EU), datasets `raw`, `dbt_staging`,
  `dbt_intermediate`, `dbt_marts`. Se mantienen los nombres existentes (dataset
  base `dbt` + schema de la capa) para no romper lo que ya los usa. Cuando este
  documento dice "marts" se refiere a `dbt_marts`.
- **CI:** `.github/workflows/ci.yml` corre pytest y `dbt parse` en cada push,
  sin conectarse a BigQuery. Ningún workflow carga datos.
- **Transformación:** dbt Core con dbt-bigquery.
- **API:** FastAPI (Python 3.11+). Toda consulta a BigQuery pasa por la API; el
  frontend nunca habla con BigQuery directamente.
- **Frontend:** Next.js (App Router) con TypeScript, Tailwind y shadcn/ui; gráficos
  con Recharts.
- **LLM:** se mantiene el proveedor actual, encapsulado en un único módulo para
  poder cambiarlo sin tocar el resto.

## Estado de la API (Fase 2)
- **Endpoints:** `/health`, `/metrics/*` (summary, mrr, mrr-movements, churn,
  retention, unit-economics), `/customers/at-risk` y `POST /ask`. Documentación
  en `/docs`.
- **Contexto del agente:** `api/agent/marts_context.md` y `marts_schema.json`
  se generan con `python -m api.agent.context`. Hay que regenerarlos cada vez
  que cambian los marts o su `schema.yml`; un test falla si quedan desfasados.
  Las pistas para el agente (cómo comparar churn, cómo explicar el NRR) van en
  las descripciones de dbt, no en el prompt.
- **LLM:** OpenAI, modelo en `LLM_MODEL` (hoy `gpt-5.4-mini`), encapsulado en
  `api/llm.py`. Variables en `.env` (ver `.env.example`).
- **Pendiente para la Fase 3:** la pantalla Customers necesita un
  `GET /customers` con búsqueda, orden y paginación.

## Estructura objetivo
```
data_generation/   generador sintético (comando único, determinístico)
dbt_insightflow/   modelos dbt: staging → intermediate → marts
api/               FastAPI: endpoints de métricas y del agente
web/               Next.js: dashboard y chat
docs/              historias de los datos, arquitectura, decisiones
agent/             app Streamlit anterior (se elimina al final)
```

## Reglas
1. **Los datos sintéticos cuentan historias.** Están documentadas en
   `docs/data-stories.md`; cualquier cambio en el generador debe mantenerlas y
   los tests deben verificarlas.
2. **Nunca exponer secretos.** Credenciales en `.env` (no versionado) y en
   secretos del hosting. No mostrar el contenido de `.env` en pantalla.
3. **El agente solo lee la capa `marts`,** solo con SELECT, con validación de la
   consulta antes de ejecutarla y con `maximum_bytes_billed` configurado.
4. **Costo casi cero.** Como los datos son estáticos, la API cachea resultados de
   métricas en memoria. Ninguna consulta debe escanear más de lo necesario.
5. **Cada fase termina con tests pasando** y la documentación actualizada.
6. **Commits pequeños,** uno por paso completado.

## Comandos (se completan a medida que se construyen)
- Generar y cargar datos: `python -m data_generation.build --end-month 2026-08`
  (`--dry-run` solo escribe Parquet en `data_generation/output/`)
- dbt: `cd dbt_insightflow && dbt build --profiles-dir .`
- Tests de Python: `pytest`
- Chequeo de dbt sin BigQuery (lo que corre el CI):
  `cd dbt_insightflow && dbt parse --profiles-dir .`
- API: `uvicorn api.main:app --reload`
- Regenerar el contexto del agente: `python -m api.agent.context`
- Pruebas de las historias con BigQuery y el LLM (a mano): `pytest -m live`
- Frontend: `cd web && npm run dev`

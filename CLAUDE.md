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
- [x] Fase 3: frontend en Next.js
- [x] Fase 4: despliegue (API en Cloud Run, frontend en Vercel)

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
- **Idioma:** código, datos y modelos en inglés. La UI es bilingüe: inglés en `/`
  (por defecto, portfolio internacional) y español de Argentina en `/es` (demos
  para pymes).
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
- **Frontend:** Next.js (App Router) con TypeScript y Tailwind, a partir del
  template "Dashboard" de Tremor (MIT, en `web/`). Se reutilizan sus componentes
  (Tremor Raw, copiados en el repo); no se instala `@tremor/react` ni otra librería
  de componentes o gráficos. Los gráficos que faltan se hacen con Recharts. npm como
  gestor de paquetes.
- **Versiones del frontend:** se migra a las últimas versiones mayores (Next.js,
  React, Tailwind, Recharts y demás) al comienzo de la Fase 3, después de limpiar el
  template y antes de aplicar el sistema de diseño. Reemplaza la regla original de
  `PROMPT_3` ("no migres a versiones mayores"): se decidió así para no construir
  las pantallas dos veces y resolver las vulnerabilidades de Next 14.
- **Sistema de diseño** (aprobado): concepto "informe de analista". Modo claro por
  defecto (no sigue al sistema; el tema elegido se recuerda). Neutros cálidos
  (Paper, Ink, Graphite), acento Ochre, Gain/Loss solo para mejora/empeora (con
  flecha y signo). Paleta de datos validada con el script de dataviz: ocre, turquesa,
  ciruela, azul, en ese orden. Tipografía: Newsreader solo para las frases de
  hallazgo, IBM Plex Sans para interfaz y números (cifras tabulares también en los
  KPI). Un único elemento audaz: el hallazgo principal con el dato en marcador ocre.
  Sin sombras ni degradados; separación con líneas finas.
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
- **Formatos por idioma en el agente:** el prompt de respuesta pide los formatos
  del idioma de la pregunta, y el control de números lee coma decimal, puntos de
  miles y "mil"/"M".

## Estado del frontend (Fase 3)
- **Una sola página** (decisión del usuario, en lugar de cinco secciones): arriba
  "Ask InsightFlow" (el agente, protagonista, única caja de la página), después
  la frase principal y los KPI, y seis secciones: tendencia de MRR, cascada del
  último mes, MRR por plan, bajas de Starter contra otros planes, retorno por
  canal (LTV/CAC) y clientes con uso en caída.
- **Idiomas:** `src/lib/i18n.ts` tiene todos los textos; `src/lib/format.ts`
  formatea por idioma (único lugar donde un número se vuelve texto);
  `src/proxy.ts` marca el idioma para `<html lang>`.
- **Datos:** las secciones son server components que piden sus datos a la API
  (`API_URL`); el chat llama a la API desde el navegador (`NEXT_PUBLIC_API_URL`,
  requiere que el origen esté en `ALLOWED_ORIGINS`). Las páginas son dinámicas
  para que un build sin API no deje cacheado el estado de error.
- **Referencia de diseño:** `/styleguide` (en inglés), enlazada desde el pie.
- **En Windows local** el puerto 8000 está reservado por el sistema: la API corre
  en 8765 (`web/.env.local` apunta ahí).

## Estado del despliegue (Fase 4)
- **Web:** https://insight-flow-five-beta.vercel.app (Vercel, raíz `web`, se
  publica con cada push a `main`). Variables `API_URL` y `NEXT_PUBLIC_API_URL`
  con la URL de la API; la segunda queda dentro del código del navegador, así
  que cambiarla requiere redeploy.
- **API:** https://insightflow-api-936762673660.europe-west1.run.app (Cloud Run,
  `europe-west1`, servicio `insightflow-api`, 0 a 1 instancia). Redeploy:
  `gcloud run deploy insightflow-api --source . --region europe-west1 --project insightflow-analytics-489617`
  (conserva la configuración). `ALLOWED_ORIGINS` tiene el dominio de Vercel y
  localhost; si cambia el dominio, actualizarlo con
  `gcloud run services update ... --update-env-vars`.
- **Permisos:** cuenta de servicio `insightflow-api@...` con
  `bigquery.jobUser` en el proyecto y lectura solo sobre `dbt_marts`.
- **Secreto:** la key de OpenAI está en Secret Manager (`openai-api-key`).
  Para rotarla: `gcloud secrets versions add openai-api-key --data-file=-` y
  redeploy.
- **Logs:** `/ask` escribe a stdout (`ASK_LOG_PATH=-`) y se lee en Cloud
  Logging con `jsonPayload.message="ask"`.
- **Costos:** facturación activa con alerta de presupuesto de US$5 (avisos al
  50, 90 y 100%). Los datasets ya no tienen vencimiento de tablas (el sandbox
  borraba las tablas a los 60 días).
- **Idioma del agente:** el chat manda `language` (`en`/`es`) y la respuesta
  usa sus formatos; una respuesta con palabras en otro alfabeto se reescribe.

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
- Frontend: `cd web && npm run dev` (tests: `npm test`; chequeos: `npm run lint`,
  `npm run typecheck`, `npm run build`)

import { useEffect, useMemo, useState } from 'react'
import * as XLSX from 'xlsx'
import Icon from './Icon'
import './ResultsModal.css'

// Columnas exportadas a Excel (encabezado legible -> valor por fila).
const EXPORT_COLUMNS = [
  ['Fecha', r => fmtDate(r.timestamp)],
  ['Modelo', r => r.model ?? ''],
  ['Módulo', r => r.module ?? ''],
  ['Compila', r => (r.compiles ? 'sí' : 'no')],
  ['Respaldo (degradada)', r => (r.degraded ? 'sí' : 'no')],
  ['Aprendido', r => (r.learned ? 'sí' : 'no')],
  ['Fragmentos RAG', r => r.rag_fragments ?? ''],
  ['Advertencias RAG', r => r.rag_warnings ?? ''],
  ['Usó ej. aprendido', r => (r.rag_used_learned === true ? 'sí' : r.rag_used_learned === false ? 'no' : '')],
  ['Lecciones globales', r => (r.global_lessons_enabled === true ? 'ON' : r.global_lessons_enabled === false ? 'OFF' : '')],
  ['Lecc. glob. inyectadas', r => r.rag_global_lessons ?? ''],
  ['Tests aprobados', r => r.tests_passed ?? 0],
  ['Tests totales', r => r.tests_total ?? 0],
  ['Tests fallidos', r => r.tests_failed ?? 0],
  ['Pass rate (%)', r => r.pass_rate ?? ''],
  ['Cob. línea (%)', r => r.line_coverage ?? ''],
  ['Cob. rama (%)', r => r.branch_coverage ?? ''],
  ['Funciones cubiertas', r => r.funcs_covered ?? 0],
  ['Funciones totales', r => r.funcs_total ?? 0],
  ['Cob. func. (%)', r => r.func_coverage_pct ?? ''],
  ['Given-When-Then', r => (r.given_when_then ? 'sí' : 'no')],
  ['Smells', r => r.smells_count ?? 0],
  ['Detalle smells', r => r.smells ?? ''],
  ['Tiempo (s)', r => r.time_s ?? ''],
  ['LLM (s)', r => r.llm_s ?? ''],
  ['LLM (% del total)', r => (r.llm_s != null && r.time_s ? Math.round((r.llm_s / r.time_s) * 100) : '')],
]

function fmtDate(iso) {
  if (!iso) return '—'
  const d = new Date(iso)
  if (isNaN(d.getTime())) return iso
  return d.toLocaleString([], {
    day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
  })
}

function pct(v) {
  return v === null || v === undefined ? '—' : `${v}%`
}

// Verde/ámbar/rojo según el valor (mismo criterio que MetricsPanel).
function rateClass(v) {
  if (v === null || v === undefined) return ''
  if (v >= 80) return 'good'
  if (v >= 50) return 'warn'
  return 'bad'
}

function avg(nums) {
  const xs = nums.filter(n => typeof n === 'number')
  if (!xs.length) return null
  return Math.round((xs.reduce((a, b) => a + b, 0) / xs.length) * 10) / 10
}

function Stat({ label, value, cls = '' }) {
  return (
    <div className="rm-stat">
      <div className={`rm-stat-v ${cls}`}>{value}</div>
      <div className="rm-stat-l">{label}</div>
    </div>
  )
}

export default function ResultsModal({ onClose }) {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState('')
  const [modelFilter, setModelFilter] = useState('all')

  function load() {
    setRows(null)
    setError('')
    fetch('/api/results')
      .then(r => (r.ok ? r.json() : Promise.reject(new Error(`HTTP ${r.status}`))))
      .then(d => setRows(d.results ?? []))
      .catch(e => setError(e.message ?? 'Error al cargar'))
  }

  useEffect(() => { load() }, [])

  // Cerrar con Escape.
  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  const models = useMemo(() => {
    const set = new Set((rows ?? []).map(r => r.model).filter(Boolean))
    return ['all', ...set]
  }, [rows])

  const filtered = useMemo(() => {
    const list = rows ?? []
    const f = modelFilter === 'all' ? list : list.filter(r => r.model === modelFilter)
    return [...f].reverse() // más reciente primero
  }, [rows, modelFilter])

  function exportExcel() {
    if (!filtered.length) return
    const header = EXPORT_COLUMNS.map(([label]) => label)
    const data = filtered.map(r => EXPORT_COLUMNS.map(([, get]) => get(r)))
    const ws = XLSX.utils.aoa_to_sheet([header, ...data])
    ws['!cols'] = header.map((_, i) => ({
      wch: Math.max(header[i].length, ...data.map(row => String(row[i] ?? '').length)) + 2,
    }))
    const wb = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(wb, ws, 'Resultados')
    const stamp = new Date().toISOString().slice(0, 10)
    const tag = modelFilter === 'all' ? 'todos' : modelFilter
    XLSX.writeFile(wb, `resultados-${tag}-${stamp}.xlsx`)
  }

  const summary = useMemo(() => {
    if (!filtered.length) return null
    const n = filtered.length
    const compiled = filtered.filter(r => r.compiles).length
    const learned = filtered.filter(r => r.learned).length
    const degraded = filtered.filter(r => r.degraded).length
    const withTests = filtered.filter(r => (r.tests_total ?? 0) > 0)
    // Solo las corridas que registraron la señal RAG (las previas a esta
    // columna la tienen vacía y no deben contar en el %).
    const withRag = filtered.filter(r => r.rag_used_learned === true || r.rag_used_learned === false)
    // Fracción de la corrida gastada en el SLM: solo las corridas que ya
    // registran llm_s (las previas a esta columna la tienen vacía). Es la
    // señal que dice cuánto ahorraría una GPU (acelera el LLM, no el resto).
    const withLlm = filtered.filter(r => typeof r.llm_s === 'number' && r.time_s)
    return {
      n,
      compiledPct: Math.round((compiled / n) * 100),
      learnedPct: Math.round((learned / n) * 100),
      usedLearnedPct: withRag.length
        ? Math.round((withRag.filter(r => r.rag_used_learned).length / withRag.length) * 100)
        : null,
      degraded,
      passRate: avg(withTests.map(r => r.pass_rate)),
      lineCov: avg(filtered.map(r => r.line_coverage)),
      funcCov: avg(filtered.map(r => r.func_coverage_pct)),
      time: avg(filtered.map(r => r.time_s)),
      llm: avg(withLlm.map(r => r.llm_s)),
      llmPct: withLlm.length
        ? Math.round(avg(withLlm.map(r => (r.llm_s / r.time_s) * 100)))
        : null,
    }
  }, [filtered])

  return (
    <div className="rm-overlay" onMouseDown={onClose}>
      <div className="rm-modal" onMouseDown={e => e.stopPropagation()}>
        <div className="rm-head">
          <span className="rm-head-ic"><Icon name="barchart" size={18} /></span>
          <div className="rm-head-txt">
            <b>Historial de resultados</b>
            <span>Cada generación registrada en results_log.csv</span>
          </div>
          <button className="rm-icon-btn" onClick={load} title="Recargar">
            <Icon name="refresh" size={15} />
          </button>
          <button className="rm-icon-btn" onClick={onClose} title="Cerrar (Esc)">
            <Icon name="x" size={17} />
          </button>
        </div>

        {rows === null && !error && (
          <div className="rm-center">Cargando...</div>
        )}

        {error && (
          <div className="rm-center rm-error">
            <Icon name="alert" size={16} /> {error}
          </div>
        )}

        {rows && !error && rows.length === 0 && (
          <div className="rm-center">
            <div className="rm-empty-ic"><Icon name="barchart" size={34} /></div>
            <div>Aún no hay resultados registrados.</div>
            <div className="rm-dim">Genera tests y aparecerán aquí.</div>
          </div>
        )}

        {rows && rows.length > 0 && (
          <>
            <div className="rm-toolbar">
              <div className="rm-filter">
                <span>Modelo</span>
                <select value={modelFilter} onChange={e => setModelFilter(e.target.value)}>
                  {models.map(m => (
                    <option key={m} value={m}>{m === 'all' ? 'Todos' : m}</option>
                  ))}
                </select>
              </div>
              {summary && (
                <span className="rm-count">
                  {summary.n} corrida{summary.n === 1 ? '' : 's'}
                </span>
              )}
              <button
                className="rm-export-btn"
                onClick={exportExcel}
                disabled={!filtered.length}
                title="Descargar resultados en Excel (.xlsx)"
              >
                <Icon name="download" size={15} />
                <span>Descargar Excel</span>
              </button>
            </div>

            {summary && (
              <div className="rm-summary">
                <Stat label="Compila" value={`${summary.compiledPct}%`} cls={rateClass(summary.compiledPct)} />
                <Stat label="Aprendidos" value={`${summary.learnedPct}%`} />
                <Stat label="Usó ej. aprend." value={summary.usedLearnedPct !== null ? `${summary.usedLearnedPct}%` : '—'} />
                <Stat label="Pass rate prom." value={pct(summary.passRate)} cls={rateClass(summary.passRate)} />
                <Stat label="Cob. línea prom." value={pct(summary.lineCov)} cls={rateClass(summary.lineCov)} />
                <Stat label="Cob. func. prom." value={pct(summary.funcCov)} cls={rateClass(summary.funcCov)} />
                <Stat label="Degradadas" value={summary.degraded} cls={summary.degraded ? 'warn' : ''} />
                <Stat label="Tiempo prom." value={summary.time !== null ? `${summary.time}s` : '—'} />
                <Stat label="LLM prom." value={summary.llm !== null ? `${summary.llm}s` : '—'} />
                <Stat
                  label="% en LLM"
                  value={summary.llmPct !== null ? `${summary.llmPct}%` : '—'}
                  cls={summary.llmPct >= 70 ? 'warn' : ''}
                />
              </div>
            )}

            <div className="rm-table-wrap">
              <table className="rm-table">
                <thead>
                  <tr>
                    <th>Fecha</th>
                    <th>Modelo</th>
                    <th>Módulo</th>
                    <th>Estado</th>
                    <th title="¿Guardó un ejemplo verificado en el RAG?">Aprend.</th>
                    <th title="Nº de fragmentos de contexto RAG inyectados al prompt">RAG</th>
                    <th title="Nº de advertencias del módulo inyectadas (cobertura/smells/aserción)">Adv.</th>
                    <th title="¿El contexto incluyó el ejemplo aprendido propio del módulo?">Usó ej.</th>
                    <th title="¿Se pidió usar las lecciones globales en esta generación? (condición ON/OFF de la ablación)">Lecc. glob.</th>
                    <th>Tests</th>
                    <th>Pass</th>
                    <th>Cob. línea</th>
                    <th>Cob. rama</th>
                    <th>Cob. func.</th>
                    <th>GWT</th>
                    <th>Smells</th>
                    <th>Tiempo</th>
                    <th title="Tiempo gastado en el SLM (generación + reintentos + oráculo) y su % sobre el total. Es la parte que aceleraría una GPU; el resto (pytest, AST, cobertura) es CPU.">LLM</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((r, i) => (
                    <tr key={i}>
                      <td className="rm-mono rm-dim">{fmtDate(r.timestamp)}</td>
                      <td className="rm-model">{r.model}</td>
                      <td>{r.module}</td>
                      <td className="rm-nowrap">
                        <span className={`rm-badge ${r.compiles ? 'ok' : 'bad'}`}>
                          {r.compiles ? 'compila' : 'no compila'}
                        </span>
                        {r.degraded && <span className="rm-badge warn">respaldo</span>}
                      </td>
                      <td>
                        {r.learned
                          ? <span className="rm-badge accent">sí</span>
                          : <span className="rm-dim">—</span>}
                      </td>
                      <td className="rm-mono rm-dim">{r.rag_fragments ?? '—'}</td>
                      <td className={`rm-mono ${r.rag_warnings > 0 ? 'warn' : 'rm-dim'}`}>
                        {r.rag_warnings ?? '—'}
                      </td>
                      <td>
                        {r.rag_used_learned === true
                          ? <span className="rm-badge accent">sí</span>
                          : r.rag_used_learned === false
                            ? <span className="rm-dim">no</span>
                            : <span className="rm-dim">—</span>}
                      </td>
                      <td>
                        {r.global_lessons_enabled === true
                          ? <span className="rm-badge accent">ON</span>
                          : r.global_lessons_enabled === false
                            ? <span className="rm-dim">OFF</span>
                            : <span className="rm-dim">—</span>}
                      </td>
                      <td className="rm-mono">
                        {r.tests_passed ?? 0}/{r.tests_total ?? 0}
                        {r.tests_failed ? <span className="rm-fail"> ✕{r.tests_failed}</span> : null}
                      </td>
                      <td className={`rm-mono ${rateClass(r.pass_rate)}`}>{pct(r.pass_rate)}</td>
                      <td className={`rm-mono ${rateClass(r.line_coverage)}`}>{pct(r.line_coverage)}</td>
                      <td className="rm-mono rm-dim">{pct(r.branch_coverage)}</td>
                      <td className={`rm-mono ${rateClass(r.func_coverage_pct)}`}>
                        {r.funcs_covered ?? 0}/{r.funcs_total ?? 0}
                      </td>
                      <td>
                        {r.given_when_then
                          ? <Icon name="check" size={14} className="rm-ic-ok" />
                          : <span className="rm-dim">—</span>}
                      </td>
                      <td>
                        {r.smells_count > 0
                          ? <span className="rm-badge warn" title={r.smells}>{r.smells_count}</span>
                          : <span className="rm-dim">0</span>}
                      </td>
                      <td className="rm-mono rm-dim">{r.time_s}s</td>
                      <td className="rm-mono rm-dim">
                        {typeof r.llm_s === 'number'
                          ? <>{r.llm_s}s {r.time_s ? <span className="rm-dim">({Math.round((r.llm_s / r.time_s) * 100)}%)</span> : null}</>
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

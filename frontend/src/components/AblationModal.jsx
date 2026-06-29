import { useEffect, useRef, useState } from 'react'
import Icon from './Icon'
import './AblationModal.css'

function rateClass(v) {
  if (v === null || v === undefined) return ''
  if (v >= 80) return 'good'
  if (v >= 50) return 'warn'
  return 'bad'
}

// Diferencia ON - OFF para una métrica (lowerBetter: menos es mejor, p.ej. smells
// o falsos positivos → se invierte el signo "bueno").
function Delta({ on, off, lowerBetter = false }) {
  if (on === null || on === undefined || off === null || off === undefined) return <span className="am-dim">—</span>
  const d = Math.round((on - off) * 100) / 100
  const better = lowerBetter ? d < 0 : d > 0
  const worse = lowerBetter ? d > 0 : d < 0
  const cls = d === 0 ? 'am-dim' : better ? 'good' : worse ? 'bad' : ''
  const sign = d > 0 ? '+' : ''
  return <span className={cls}>{sign}{d}</span>
}

// ── Descargas (cliente, sin endpoint nuevo) ────────────────────────────────
function triggerDownload(filename, content, mime) {
  const blob = new Blob([content], { type: mime })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

function csvCell(v) {
  if (v === null || v === undefined) return ''
  const s = String(v)
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s
}

function toCSV(headers, rows) {
  const lines = [headers.join(',')]
  for (const row of rows) lines.push(headers.map(h => csvCell(row[h])).join(','))
  return lines.join('\n')
}

const STAMP = () => new Date().toISOString().slice(0, 19).replace(/[:T]/g, '-')

// Resumen ON/OFF por clase calculado en el cliente (espejo de _summary del
// backend). Permite mostrar resultados y habilitar descargas aunque el proceso
// se detenga a media corrida (no llega el evento `done`).
function computeStats(rs) {
  const mean = (k) => {
    const vals = rs.map(r => r[k]).filter(v => v !== null && v !== undefined)
    return vals.length ? Math.round((vals.reduce((a, b) => a + b, 0) / vals.length) * 100) / 100 : null
  }
  const n = rs.length
  const bugs = rs.filter(r => r.bug_detected).length
  return {
    n,
    pass_rate: mean('pass_rate'),
    line_coverage: mean('line_coverage'),
    func_coverage: mean('func_coverage_pct'),
    smells: mean('smells'),
    bug_detected_rate: n ? Math.round((bugs / n) * 1000) / 10 : null,
    elapsed: mean('elapsed'),
  }
}

function computeSummary(runs) {
  const ok = runs.filter(r => !r.failed)
  const out = {}
  for (const label of ['correcto', 'incorrecto']) {
    out[label] = {}
    for (const cond of ['ON', 'OFF']) {
      out[label][cond] = computeStats(ok.filter(r => r.label === label && r.cond === cond))
    }
  }
  return out
}

// Filas de resumen por clase para descarga / render.
const SUMMARY_ROWS = {
  correcto: [
    { key: 'pass_rate', label: 'Pass rate', rate: true },
    { key: 'line_coverage', label: 'Cob. línea', rate: true },
    { key: 'func_coverage', label: 'Cob. función', rate: true },
    { key: 'smells', label: 'Smells (media)', lowerBetter: true },
    { key: 'bug_detected_rate', label: 'Falsos positivos %', lowerBetter: true, rate: true },
  ],
  incorrecto: [
    { key: 'bug_detected_rate', label: 'Bug detectado %', star: true, rate: true },
    { key: 'pass_rate', label: 'Pass rate', rate: true },
    { key: 'line_coverage', label: 'Cob. línea', rate: true },
    { key: 'smells', label: 'Smells (media)', lowerBetter: true },
  ],
}

const DETAIL_COLS = [
  'i', 'cond', 'label', 'module', 'pass_rate', 'line_coverage', 'branch_coverage',
  'func_coverage_pct', 'smells', 'given_when_then', 'tests_total', 'tests_passed',
  'tests_failed', 'tests_errors', 'potential_bugs', 'bug_detected',
  'lessons_injected', 'compiles', 'degraded', 'elapsed',
]

export default function AblationModal({ models, defaultModel, onClose }) {
  const [correctos, setCorrectos] = useState([])
  const [incorrectos, setIncorrectos] = useState([])
  const [model, setModel] = useState(defaultModel || (models[0] ?? ''))
  const [reps, setReps] = useState(5)
  const [running, setRunning] = useState(false)
  const [meta, setMeta] = useState(null)        // evento start
  const [runs, setRuns] = useState([])
  const [summary, setSummary] = useState(null)
  const [stopped, setStopped] = useState(false)
  const [error, setError] = useState('')

  const abortRef = useRef(null)

  useEffect(() => {
    function onKey(e) { if (e.key === 'Escape' && !running) onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose, running])

  function handleEvent(msg) {
    if (msg.type === 'start') setMeta(msg)
    else if (msg.type === 'run') setRuns(prev => [...prev, msg])
    else if (msg.type === 'run_error') setRuns(prev => [...prev, { ...msg, failed: true }])
    else if (msg.type === 'done') setSummary(msg.summary)
  }

  const totalFiles = correctos.length + incorrectos.length

  async function run() {
    if (!totalFiles || !model || running) return
    setRunning(true)
    setMeta(null); setRuns([]); setSummary(null); setStopped(false); setError('')

    const controller = new AbortController()
    abortRef.current = controller

    const form = new FormData()
    correctos.forEach(f => form.append('correctos', f))
    incorrectos.forEach(f => form.append('incorrectos', f))
    form.append('model', model)
    form.append('reps', reps)

    try {
      const resp = await fetch('/api/ablation/run', { method: 'POST', body: form, signal: controller.signal })
      if (!resp.ok) throw new Error((await resp.text()) || `HTTP ${resp.status}`)
      const reader = resp.body.getReader()
      const dec = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += dec.decode(value, { stream: true })
        let idx
        while ((idx = buffer.indexOf('\n')) >= 0) {
          const line = buffer.slice(0, idx).trim()
          buffer = buffer.slice(idx + 1)
          if (line) handleEvent(JSON.parse(line))
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') setError(e.message ?? 'Error en la ablación')
    } finally {
      setRunning(false)
    }
  }

  // Detener: corta el stream y trata lo ya corrido como resultado final
  // (calcula el resumen en el cliente y habilita las descargas). El backend
  // ejecuta su finally → _restore() al cerrarse la conexión, así los stores
  // quedan limpios igual que en una corrida completa.
  function handleStop() {
    setStopped(true)
    abortRef.current?.abort()
    setRuns(prev => {
      if (prev.length) setSummary(computeSummary(prev))
      return prev
    })
  }

  function handleClose() {
    if (running) abortRef.current?.abort()
    onClose()
  }

  // ── Descargas ──────────────────────────────────────────────────────────
  function downloadSummary() {
    if (!summary) return
    const headers = ['clase', 'metrica', 'ON', 'OFF', 'delta']
    const rows = []
    for (const label of ['correcto', 'incorrecto']) {
      const blk = summary[label]
      if (!blk) continue
      rows.push({ clase: label, metrica: 'n_corridas', ON: blk.ON?.n, OFF: blk.OFF?.n, delta: '' })
      for (const { key, label: name } of SUMMARY_ROWS[label]) {
        const on = blk.ON?.[key], off = blk.OFF?.[key]
        const delta = (on != null && off != null) ? Math.round((on - off) * 100) / 100 : ''
        rows.push({ clase: label, metrica: name, ON: on ?? '', OFF: off ?? '', delta })
      }
    }
    triggerDownload(`ablacion-resumen-${STAMP()}.csv`, toCSV(headers, rows), 'text/csv;charset=utf-8')
  }

  function downloadDetail() {
    const ok = runs.filter(r => !r.failed)
    if (!ok.length) return
    triggerDownload(`ablacion-detalle-${STAMP()}.csv`, toCSV(DETAIL_COLS, ok), 'text/csv;charset=utf-8')
  }

  function downloadBundle() {
    const ok = runs.filter(r => !r.failed)
    if (!ok.length) return
    const bundle = ok.map(r => ({
      i: r.i, module: r.module, label: r.label, cond: r.cond,
      lessons_injected: r.lessons_injected,
      metrics: {
        pass_rate: r.pass_rate, line_coverage: r.line_coverage,
        smells: r.smells, bug_detected: r.bug_detected,
      },
      context_rag: r.context || [],
      tests_code: r.tests || '',
    }))
    triggerDownload(`ablacion-codigo-contexto-${STAMP()}.json`, JSON.stringify(bundle, null, 2), 'application/json')
  }

  const done = runs.length
  const total = meta?.total ?? 0
  const pct = total ? Math.round((done / total) * 100) : 0

  return (
    <div className="am-overlay" onMouseDown={handleClose}>
      <div className="am-modal" onMouseDown={e => e.stopPropagation()}>
        <div className="am-head">
          <span className="am-head-ic"><Icon name="sparkles" size={18} /></span>
          <div className="am-head-txt">
            <b>Ablación de lecciones globales</b>
            <span>Compara la generación con lecciones ON vs OFF, separando correctos / incorrectos</span>
          </div>
          <button className="am-icon-btn" onClick={handleClose} title={running ? 'Detener y cerrar' : 'Cerrar (Esc)'}>
            <Icon name="x" size={17} />
          </button>
        </div>

        {/* Configuración */}
        <div className="am-config">
          <label className="am-field am-file">
            <span>Correctos (.py)</span>
            <input
              type="file" accept=".py" multiple disabled={running}
              onChange={e => setCorrectos(Array.from(e.target.files))}
            />
            <span className="am-file-names">
              {correctos.length ? `${correctos.length} archivo(s)` : 'Ninguno'}
            </span>
          </label>
          <label className="am-field am-file">
            <span>Incorrectos (.py)</span>
            <input
              type="file" accept=".py" multiple disabled={running}
              onChange={e => setIncorrectos(Array.from(e.target.files))}
            />
            <span className="am-file-names">
              {incorrectos.length ? `${incorrectos.length} archivo(s)` : 'Ninguno'}
            </span>
          </label>
          <label className="am-field">
            <span>Modelo</span>
            <select value={model} disabled={running} onChange={e => setModel(e.target.value)}>
              {models.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </label>
          <label className="am-field am-reps">
            <span>Repeticiones</span>
            <input
              type="number" min={1} max={20} value={reps} disabled={running}
              onChange={e => setReps(Math.max(1, Math.min(20, Number(e.target.value) || 1)))}
            />
          </label>
          {running ? (
            <button className="am-stop-btn" onClick={handleStop} title="Detener y conservar lo ya corrido">
              <Icon name="stop" size={15} />
              Detener
            </button>
          ) : (
            <button className="am-run-btn" onClick={run} disabled={!totalFiles || !model}>
              <Icon name="sparkles" size={15} />
              Ejecutar ablación
            </button>
          )}
        </div>

        {totalFiles > 0 && !running && !meta && (
          <div className="am-estimate">
            {correctos.length} correcto(s) + {incorrectos.length} incorrecto(s) × {reps} rep × 2 condiciones
            = <b>{totalFiles * reps * 2} corridas</b>. En CPU pueden tardar varias horas; no cierres esta ventana.
          </div>
        )}

        {error && <div className="am-error"><Icon name="alert" size={15} /> {error}</div>}

        {/* Progreso */}
        {meta && (
          <div className="am-progress">
            <div className="am-progress-bar">
              <div className="am-progress-fill" style={{ width: `${pct}%` }} />
            </div>
            <div className="am-progress-txt">
              {done}/{total} corridas {running && <span className="am-live">●</span>}
              {summary && <span className="am-done-tag">{stopped ? 'detenido — resultados parciales' : 'completado'}</span>}
            </div>
          </div>
        )}

        {/* Resumen ON vs OFF por clase + descargas */}
        {summary && (
          <div className="am-summary">
            <div className="am-sum-grid">
              {['incorrecto', 'correcto'].map(label => {
                const blk = summary[label]
                if (!blk) return null
                return (
                  <div className="am-sum-block" key={label}>
                    <div className="am-sum-title">
                      <span className={`am-badge cls-${label}`}>{label === 'incorrecto' ? 'Incorrectos' : 'Correctos'}</span>
                      <span className="am-dim">{blk.ON?.n ?? 0} ON · {blk.OFF?.n ?? 0} OFF</span>
                    </div>
                    <table className="am-sum-table">
                      <thead>
                        <tr><th></th><th>ON</th><th>OFF</th><th>Δ</th></tr>
                      </thead>
                      <tbody>
                        {SUMMARY_ROWS[label].map(({ key, label: name, lowerBetter, rate, star }) => (
                          <tr key={key} className={star ? 'am-star-row' : ''}>
                            <td>{star && <Icon name="bug" size={12} />} {name}</td>
                            <td className={rate ? rateClass(blk.ON?.[key]) : ''}>{blk.ON?.[key] ?? '—'}</td>
                            <td className={rate ? rateClass(blk.OFF?.[key]) : ''}>{blk.OFF?.[key] ?? '—'}</td>
                            <td><Delta on={blk.ON?.[key]} off={blk.OFF?.[key]} lowerBetter={lowerBetter} /></td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )
              })}
            </div>

            <div className="am-downloads">
              <button className="am-dl-btn" onClick={downloadSummary} title="Resumen ON/OFF por clase">
                <Icon name="download" size={14} /> Resumen (CSV)
              </button>
              <button className="am-dl-btn" onClick={downloadDetail} title="Una fila por corrida con todas las métricas">
                <Icon name="download" size={14} /> Detalle por corrida (CSV)
              </button>
              <button className="am-dl-btn" onClick={downloadBundle} title="Código generado + contexto RAG de cada corrida">
                <Icon name="filecode" size={14} /> Código + contexto (JSON)
              </button>
            </div>
            <div className="am-hint">
              Δ verde = ON mejora. En incorrectos, "Bug detectado %" es la señal clave (mayor = mejor).
              En correctos, "Falsos positivos %" mide tests que fallan sobre código correcto (menor = mejor).
            </div>
          </div>
        )}

        {/* Corridas en vivo */}
        {runs.length > 0 && (
          <div className="am-runs-wrap">
            <table className="am-runs">
              <thead>
                <tr>
                  <th>#</th><th>Cond</th><th>Clase</th><th>Módulo</th><th>Pass</th>
                  <th>Cob.</th><th>Smells</th><th>Bug</th><th>Lecc.</th><th>Tiempo</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r, i) => (
                  <tr key={i} className={r.failed ? 'am-row-fail' : ''}>
                    <td className="am-dim">{r.i}</td>
                    <td><span className={`am-badge ${r.cond === 'ON' ? 'on' : 'off'}`}>{r.cond}</span></td>
                    <td><span className={`am-badge cls-${r.label}`}>{r.label === 'incorrecto' ? 'inc' : 'cor'}</span></td>
                    <td>{r.module}</td>
                    {r.failed ? (
                      <td colSpan={6} className="am-fail-msg">{r.message}</td>
                    ) : (
                      <>
                        <td className={rateClass(r.pass_rate)}>{r.pass_rate ?? '—'}</td>
                        <td className={rateClass(r.line_coverage)}>{r.line_coverage ?? '—'}</td>
                        <td>{r.smells > 0 ? <span className="am-badge warn">{r.smells}</span> : <span className="am-dim">0</span>}</td>
                        <td>
                          {r.bug_detected
                            ? <span className={r.label === 'incorrecto' ? 'good' : 'bad'}><Icon name="check" size={13} /></span>
                            : <span className="am-dim">—</span>}
                        </td>
                        <td className="am-dim">{r.lessons_injected}</td>
                        <td className="am-dim">{r.elapsed}s</td>
                      </>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}

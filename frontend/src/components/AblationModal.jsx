import { useEffect, useRef, useState } from 'react'
import Icon from './Icon'
import './AblationModal.css'

function rateClass(v) {
  if (v === null || v === undefined) return ''
  if (v >= 80) return 'good'
  if (v >= 50) return 'warn'
  return 'bad'
}

// Diferencia ON - OFF para una métrica (smells: menos es mejor, se invierte el signo bueno).
function Delta({ on, off, lowerBetter = false }) {
  if (on === null || on === undefined || off === null || off === undefined) return <span className="am-dim">—</span>
  const d = Math.round((on - off) * 100) / 100
  const better = lowerBetter ? d < 0 : d > 0
  const worse = lowerBetter ? d > 0 : d < 0
  const cls = d === 0 ? 'am-dim' : better ? 'good' : worse ? 'bad' : ''
  const sign = d > 0 ? '+' : ''
  return <span className={cls}>{sign}{d}</span>
}

export default function AblationModal({ models, defaultModel, onClose }) {
  const [files, setFiles] = useState([])
  const [model, setModel] = useState(defaultModel || (models[0] ?? ''))
  const [reps, setReps] = useState(5)
  const [running, setRunning] = useState(false)
  const [meta, setMeta] = useState(null)        // evento start
  const [runs, setRuns] = useState([])
  const [summary, setSummary] = useState(null)
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

  async function run() {
    if (!files.length || !model || running) return
    setRunning(true)
    setMeta(null); setRuns([]); setSummary(null); setError('')

    const controller = new AbortController()
    abortRef.current = controller

    const form = new FormData()
    files.forEach(f => form.append('files', f))
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

  function handleClose() {
    if (running) abortRef.current?.abort()
    onClose()
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
            <span>Compara la generación con lecciones ON vs OFF en módulos frescos</span>
          </div>
          <button className="am-icon-btn" onClick={handleClose} title={running ? 'Detener y cerrar' : 'Cerrar (Esc)'}>
            <Icon name="x" size={17} />
          </button>
        </div>

        {/* Configuración */}
        <div className="am-config">
          <label className="am-field am-file">
            <span>Módulos (.py)</span>
            <input
              type="file" accept=".py" multiple disabled={running}
              onChange={e => setFiles(Array.from(e.target.files))}
            />
            <span className="am-file-names">
              {files.length ? files.map(f => f.name).join(', ') : 'Ninguno seleccionado'}
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
          <button className="am-run-btn" onClick={run} disabled={running || !files.length || !model}>
            <Icon name="sparkles" size={15} />
            {running ? 'Ejecutando…' : 'Ejecutar ablación'}
          </button>
        </div>

        {files.length > 0 && !running && !meta && (
          <div className="am-estimate">
            {files.length} módulo(s) × {reps} rep × 2 condiciones = <b>{files.length * reps * 2} corridas</b>.
            En CPU pueden tardar varias horas; no cierres esta ventana.
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
              {summary && <span className="am-done-tag">completado</span>}
            </div>
          </div>
        )}

        {/* Resumen ON vs OFF */}
        {summary && (
          <div className="am-summary">
            <table className="am-sum-table">
              <thead>
                <tr><th></th><th>ON</th><th>OFF</th><th>Δ (ON−OFF)</th></tr>
              </thead>
              <tbody>
                <tr>
                  <td>Corridas</td>
                  <td>{summary.ON.n}</td><td>{summary.OFF.n}</td><td className="am-dim">—</td>
                </tr>
                <tr>
                  <td>Smells (media)</td>
                  <td>{summary.ON.smells ?? '—'}</td><td>{summary.OFF.smells ?? '—'}</td>
                  <td><Delta on={summary.ON.smells} off={summary.OFF.smells} lowerBetter /></td>
                </tr>
                <tr>
                  <td>Cob. línea (media)</td>
                  <td className={rateClass(summary.ON.line_coverage)}>{summary.ON.line_coverage ?? '—'}</td>
                  <td className={rateClass(summary.OFF.line_coverage)}>{summary.OFF.line_coverage ?? '—'}</td>
                  <td><Delta on={summary.ON.line_coverage} off={summary.OFF.line_coverage} /></td>
                </tr>
                <tr>
                  <td>Pass rate (media)</td>
                  <td className={rateClass(summary.ON.pass_rate)}>{summary.ON.pass_rate ?? '—'}</td>
                  <td className={rateClass(summary.OFF.pass_rate)}>{summary.OFF.pass_rate ?? '—'}</td>
                  <td><Delta on={summary.ON.pass_rate} off={summary.OFF.pass_rate} /></td>
                </tr>
              </tbody>
            </table>
            <div className="am-hint">
              Δ verde = ON mejora. Detalle por corrida en results_log.csv (columna rag_global_lessons).
            </div>
          </div>
        )}

        {/* Corridas en vivo */}
        {runs.length > 0 && (
          <div className="am-runs-wrap">
            <table className="am-runs">
              <thead>
                <tr>
                  <th>#</th><th>Cond</th><th>Módulo</th><th>Pass</th>
                  <th>Cob.</th><th>Smells</th><th>Lecc.</th><th>Tiempo</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r, i) => (
                  <tr key={i} className={r.failed ? 'am-row-fail' : ''}>
                    <td className="am-dim">{r.i}</td>
                    <td><span className={`am-badge ${r.cond === 'ON' ? 'on' : 'off'}`}>{r.cond}</span></td>
                    <td>{r.module}</td>
                    {r.failed ? (
                      <td colSpan={5} className="am-fail-msg">{r.message}</td>
                    ) : (
                      <>
                        <td className={rateClass(r.pass_rate)}>{r.pass_rate ?? '—'}</td>
                        <td className={rateClass(r.line_coverage)}>{r.line_coverage ?? '—'}</td>
                        <td>{r.smells > 0 ? <span className="am-badge warn">{r.smells}</span> : <span className="am-dim">0</span>}</td>
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

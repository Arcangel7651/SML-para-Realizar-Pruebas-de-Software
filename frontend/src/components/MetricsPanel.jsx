import { useEffect, useState } from 'react'
import Icon from './Icon'
import './MetricsPanel.css'

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

function rateColor(rate) {
  if (rate >= 80) return 'good'
  if (rate >= 50) return 'warn'
  return 'bad'
}

function Meter({ label, value }) {
  const color = rateColor(value)
  return (
    <div className="gen-meter">
      <div className="gen-meter-top">
        <span className="gen-meter-lbl">{label}</span>
        <span className={`gen-meter-val ${color}`}>{value}%</span>
      </div>
      <div className="gen-track">
        <div className={`gen-fill ${color}`} style={{ width: `${Math.min(value, 100)}%` }} />
      </div>
    </div>
  )
}

const SMELL_LABELS = {
  assertion_roulette: 'assertion_roulette',
  empty_test:         'empty_test',
  generic_name:       'generic_name',
}

export default function MetricsPanel({ result, moduleName }) {
  const { compiles, compile_error, functions_found = [], metrics, quality, generation_time, learned, degraded, potential_bugs = [] } = result

  // Estado local de los bugs para reflejar la clasificación (triaje) sin
  // re-generar. Se resincroniza cuando llega un nuevo resultado.
  const [bugs, setBugs] = useState(potential_bugs)
  useEffect(() => { setBugs(potential_bugs) }, [result]) // eslint-disable-line react-hooks/exhaustive-deps

  // Triaje: anotación PRIVADA solo para análisis (precisión/recall). Se persiste
  // en bugs_store.json; no influye en el modelo ni en el RAG.
  async function classifyBug(bug, triage) {
    try {
      await fetch('/api/bugs/triage', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ module: moduleName, name: bug.name, detail: bug.detail, triage }),
      })
    } catch { /* el triaje es solo para análisis: si falla, se ignora */ }
    setBugs(prev => prev.map(b =>
      b.name === bug.name && b.detail === bug.detail ? { ...b, triage } : b
    ))
  }

  const stats = []
  if (metrics) {
    stats.push({ key: 'total', label: 'Total', value: metrics.tests_total, cls: 'total' })
    stats.push({ key: 'pass', label: 'Pasaron', value: metrics.tests_passed, cls: 'pass', dot: 'dot-good' })
    if (metrics.tests_failed > 0) stats.push({ key: 'fail', label: 'Fallaron', value: metrics.tests_failed, cls: 'fail', dot: 'dot-bad' })
    if (metrics.tests_skipped > 0) stats.push({ key: 'skip', label: 'Omitidos', value: metrics.tests_skipped, cls: 'skip', dot: 'dot-warn' })
    if (metrics.tests_errors > 0) stats.push({ key: 'err', label: 'Errores', value: metrics.tests_errors, cls: 'fail', dot: 'dot-bad' })
  }

  return (
    <>
      <div className="gen-mhead">
        <span className="gen-mtitle">Evaluación de resultados</span>
        <div className="gen-mhead-right">
          {degraded && (
            <span className="gen-degraded-pill" title="El código generado no compiló: se rescataron los tests válidos y se completó con pytest.skip() para las funciones sin test">
              <Icon name="alert" size={13} /> Suite de respaldo (rescate parcial)
            </span>
          )}
          {learned && (
            <span className="gen-learned-pill" title="Este resultado se guardó como nuevo ejemplo en el contexto RAG">
              <Icon name="database" size={13} /> Aprendido y guardado en RAG
            </span>
          )}
          {generation_time !== undefined && (
            <span className="gen-mtime"><Icon name="timer" size={13} /> {formatDuration(generation_time)}</span>
          )}
        </div>
      </div>

      {bugs.length > 0 && (
        <div className="gen-bugs">
          <div className="gen-bugs-head">
            <span className="gen-bugs-ic"><Icon name="bug" size={16} /></span>
            <div className="gen-bugs-head-txt">
              <b>{bugs.length} posible{bugs.length === 1 ? '' : 's'} bug{bugs.length === 1 ? '' : 's'} detectado{bugs.length === 1 ? '' : 's'}</b>
              <span>Tests que fallaron en esta o en anteriores generaciones de este módulo: o el código tiene un bug, o la aserción del modelo es incorrecta. Clasifícalos para tu análisis.</span>
            </div>
          </div>
          <div className="gen-bugs-list">
            {bugs.map((bug, i) => (
              <div key={`${bug.name}-${i}`} className="gen-bug">
                <span className="gen-bug-name">
                  {bug.name}
                  {bug.seen_now === false && <span className="gen-bug-tag">run anterior</span>}
                </span>
                <span className="gen-bug-detail">{bug.detail}</span>
                <div className="gen-bug-triage">
                  <button
                    className={`gen-triage-btn real${bug.triage === 'bug_real' ? ' active' : ''}`}
                    onClick={() => classifyBug(bug, bug.triage === 'bug_real' ? null : 'bug_real')}
                  >
                    <Icon name="bug" size={12} /> Bug real
                  </button>
                  <button
                    className={`gen-triage-btn falso${bug.triage === 'falso_positivo' ? ' active' : ''}`}
                    onClick={() => classifyBug(bug, bug.triage === 'falso_positivo' ? null : 'falso_positivo')}
                  >
                    <Icon name="check" size={12} /> Falso positivo
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="gen-mgrid">
        {/* Compilación */}
        <div className="gen-card">
          <div className="gen-card-head"><Icon name="shield" /> Compilación</div>
          <div className="gen-status">
            <span className={`gen-status-ic ${compiles ? 'ok' : 'bad'}`}>
              <Icon name={compiles ? 'check' : 'alert'} size={18} />
            </span>
            <div className="gen-status-txt">
              <b>{compiles ? 'Código válido' : 'Error de sintaxis'}</b>
              {compile_error && <span className="mono-error">{compile_error}</span>}
            </div>
          </div>
        </div>

        {/* Funciones analizadas */}
        {functions_found.length > 0 && (
          <div className="gen-card">
            <div className="gen-card-head"><Icon name="function" /> Funciones analizadas</div>
            <div className="gen-chips">
              {functions_found.map(fn => {
                const count = quality?.tests_per_function?.[fn]
                return (
                  <span key={fn} className="gen-chip">
                    {fn}
                    {count !== undefined && (
                      <span className="cnt">{count} {count === 1 ? 'test' : 'tests'}</span>
                    )}
                  </span>
                )
              })}
            </div>
          </div>
        )}

        {/* Resultados de pytest */}
        {metrics ? (
          <div className="gen-card gen-card-span2">
            <div className="gen-card-head"><Icon name="gauge" /> Resultados de pytest</div>

            {metrics.tests_total === 0 && metrics.run_summary ? (
              <div className="gen-run-summary">
                <span className="muted">Pytest no ejecutó tests</span>
                <span className="mono-error">{metrics.run_summary}</span>
              </div>
            ) : (
              <div className="gen-stats">
                {stats.map(s => (
                  <div key={s.key} className={`gen-stat ${s.cls}`}>
                    <div className="v">{s.value}</div>
                    <div className="l">{s.dot && <span className={`dot ${s.dot}`} />} {s.label}</div>
                  </div>
                ))}
              </div>
            )}

            <Meter label="Pass rate" value={metrics.pass_rate} />
            <Meter
              label={`Cobertura de línea${metrics.branch_coverage !== null && metrics.branch_coverage !== undefined ? ' + rama' : ''}`}
              value={metrics.line_coverage}
            />
            {metrics.branch_coverage !== null && metrics.branch_coverage !== undefined && (
              <Meter label="Cobertura de ramas" value={metrics.branch_coverage} />
            )}
          </div>
        ) : compiles && (
          <div className="gen-card gen-card-span2">
            <div className="gen-card-head"><Icon name="gauge" /> Resultados de pytest</div>
            <span className="muted">Evaluación pytest no ejecutada</span>
          </div>
        )}

        {/* Calidad */}
        {quality && (
          <div className="gen-card gen-card-span2">
            <div className="gen-card-head"><Icon name="list" /> Calidad</div>
            <div className="gen-checklist">
              <div className="gen-check">
                <span className={`gen-check-ic ${quality.is_clean_output ? 'ok' : 'warn'}`}>
                  <Icon name={quality.is_clean_output ? 'check' : 'alert'} />
                </span>
                <div className="gen-check-body">
                  <span className="gen-check-lbl">Solo código ejecutable <span className="gen-rule">OR-1</span></span>
                </div>
                <span className={`gen-check-val ${quality.is_clean_output ? 'ok' : 'warn'}`}>
                  {quality.is_clean_output ? 'Sin texto/markdown mezclado' : 'Hay restos de markdown o texto'}
                </span>
              </div>

              <div className="gen-check">
                <span className={`gen-check-ic ${quality.starts_with_import_pytest ? 'ok' : 'warn'}`}>
                  <Icon name={quality.starts_with_import_pytest ? 'check' : 'alert'} />
                </span>
                <div className="gen-check-body">
                  <span className="gen-check-lbl">Empieza con <code>import pytest</code> <span className="gen-rule">OR-2</span></span>
                </div>
                <span className={`gen-check-val ${quality.starts_with_import_pytest ? 'ok' : 'warn'}`}>
                  {quality.starts_with_import_pytest ? 'Cumple' : 'No cumple'}
                </span>
              </div>

              <div className="gen-check">
                <span className={`gen-check-ic ${quality.has_expected_test_class ? 'ok' : 'warn'}`}>
                  <Icon name={quality.has_expected_test_class ? 'check' : 'alert'} />
                </span>
                <div className="gen-check-body">
                  <span className="gen-check-lbl">
                    Clase {quality.expected_class_name ? <code>{quality.expected_class_name}</code> : 'Test<Módulo>'} única <span className="gen-rule">OR-3</span>
                  </span>
                </div>
                <span className={`gen-check-val ${quality.has_expected_test_class ? 'ok' : 'warn'}`}>
                  {quality.has_expected_test_class ? 'Presente' : 'Ausente o incorrecta'}
                </span>
              </div>

              <div className="gen-check">
                <span className={`gen-check-ic ${quality.has_given_when_then ? 'ok' : 'warn'}`}>
                  <Icon name={quality.has_given_when_then ? 'check' : 'alert'} />
                </span>
                <div className="gen-check-body">
                  <span className="gen-check-lbl">Given/When/Then <span className="gen-rule">OR-5</span></span>
                </div>
                <span className={`gen-check-val ${quality.has_given_when_then ? 'ok' : 'warn'}`}>
                  {quality.has_given_when_then ? 'Presente' : 'Ausente'}
                </span>
              </div>

              <div className="gen-check">
                <span className={`gen-check-ic ${quality.smells_detected.length === 0 ? 'ok' : 'warn'}`}>
                  <Icon name={quality.smells_detected.length === 0 ? 'check' : 'alert'} />
                </span>
                <div className="gen-check-body">
                  <span className="gen-check-lbl">Test smells</span>
                  {quality.smells_detected.length > 0 && (
                    <div className="gen-smells">
                      {quality.smells_detected.map(smell => (
                        <span key={smell} className="gen-smell">
                          <Icon name="alert" size={12} /> {SMELL_LABELS[smell] ?? smell}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
                <span className={`gen-check-val ${quality.smells_detected.length === 0 ? 'ok' : 'warn'}`}>
                  {quality.smells_detected.length === 0 ? 'Ninguno detectado' : `${quality.smells_detected.length} detectado(s)`}
                </span>
              </div>
            </div>
          </div>
        )}
      </div>
    </>
  )
}

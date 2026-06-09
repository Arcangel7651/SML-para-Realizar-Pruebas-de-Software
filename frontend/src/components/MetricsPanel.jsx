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

function ProgressBar({ value, color }) {
  return (
    <div className="progress-track">
      <div
        className={`progress-fill progress-${color}`}
        style={{ width: `${Math.min(value, 100)}%` }}
      />
    </div>
  )
}

const SMELL_LABELS = {
  assertion_roulette: 'assertion_roulette',
  empty_test:         'empty_test',
  generic_name:       'generic_name',
}

export default function MetricsPanel({ result }) {
  const { compiles, compile_error, functions_found = [], metrics, quality, generation_time } = result

  return (
    <div className="metrics-panel">

      {/* ── Header ── */}
      <div className="metrics-header">
        <span className="metrics-title">EVALUACIÓN DE RESULTADOS</span>
        {generation_time !== undefined && (
          <span className="generation-time">⏱ {formatDuration(generation_time)}</span>
        )}
      </div>

      {/* ── Funciones detectadas ── */}
      {functions_found.length > 0 && (
        <div className="report-row">
          <span className="report-label">Funciones analizadas</span>
          <div className="chip-list">
            {functions_found.map(fn => {
              const count = quality?.tests_per_function?.[fn]
              return (
                <span key={fn} className="chip">
                  {fn}
                  {count !== undefined && (
                    <span className="chip-count">
                      {count} {count === 1 ? 'test' : 'tests'}
                    </span>
                  )}
                </span>
              )
            })}
          </div>
        </div>
      )}

      <div className="report-divider" />

      {/* ── Compilación ── */}
      <div className="report-row">
        <span className="report-label">Compilación</span>
        {compiles
          ? <span className="stat-ok">✓ Código válido</span>
          : <span className="stat-bad">✗ Error de sintaxis</span>
        }
      </div>
      {compile_error && (
        <div className="report-row compile-error-row">
          <span className="report-label" />
          <span className="mono-error">{compile_error}</span>
        </div>
      )}

      {/* ── Métricas pytest ── */}
      {metrics ? (
        <>
          <div className="report-divider" />

          <div className="report-row">
            <span className="report-label">Tests ejecutados</span>
            <span className="stat-value">{metrics.tests_total}</span>
          </div>

          <div className="report-row indent">
            <span className="report-label">
              <span className="dot dot-good" /> Pasaron
            </span>
            <span className="stat-ok">{metrics.tests_passed}</span>
          </div>

          {metrics.tests_failed > 0 && (
            <div className="report-row indent">
              <span className="report-label">
                <span className="dot dot-bad" /> Fallaron
              </span>
              <span className="stat-bad">{metrics.tests_failed}</span>
            </div>
          )}

          {metrics.tests_skipped > 0 && (
            <div className="report-row indent">
              <span className="report-label">
                <span className="dot dot-warn" /> Omitidos
              </span>
              <span className="stat-warn">{metrics.tests_skipped}</span>
            </div>
          )}

          {metrics.tests_errors > 0 && (
            <div className="report-row indent">
              <span className="report-label">
                <span className="dot dot-bad" /> Errores
              </span>
              <span className="stat-bad">{metrics.tests_errors}</span>
            </div>
          )}

          {metrics.tests_total === 0 && metrics.run_summary && (
            <div className="report-row compile-error-row">
              <span className="report-label muted">Pytest no ejecutó tests</span>
              <span className="mono-error">{metrics.run_summary}</span>
            </div>
          )}

          <div className="report-divider" />

          <div className="report-row">
            <span className="report-label">Pass rate</span>
            <span className={`stat-value stat-${rateColor(metrics.pass_rate)}`}>
              {metrics.pass_rate}%
            </span>
          </div>
          <div className="report-row progress-row">
            <ProgressBar value={metrics.pass_rate} color={rateColor(metrics.pass_rate)} />
          </div>

          <div className="report-row">
            <span className="report-label">
              Cobertura de línea{metrics.branch_coverage !== null && metrics.branch_coverage !== undefined ? ' + rama' : ''}
            </span>
            <span className={`stat-value stat-${rateColor(metrics.line_coverage)}`}>
              {metrics.line_coverage}%
            </span>
          </div>
          <div className="report-row progress-row">
            <ProgressBar value={metrics.line_coverage} color={rateColor(metrics.line_coverage)} />
          </div>

          {metrics.branch_coverage !== null && metrics.branch_coverage !== undefined && (
            <>
              <div className="report-row">
                <span className="report-label">Cobertura de ramas</span>
                <span className={`stat-value stat-${rateColor(metrics.branch_coverage)}`}>
                  {metrics.branch_coverage}%
                </span>
              </div>
              <div className="report-row progress-row">
                <ProgressBar value={metrics.branch_coverage} color={rateColor(metrics.branch_coverage)} />
              </div>
            </>
          )}
        </>
      ) : compiles && (
        <>
          <div className="report-divider" />
          <div className="report-row">
            <span className="report-label muted">Evaluación pytest</span>
            <span className="muted">no ejecutada</span>
          </div>
        </>
      )}

      {/* ── Calidad ── */}
      {quality && (
        <>
          <div className="report-divider" />
          <div className="report-row">
            <span className="report-label">Calidad</span>
          </div>

          <div className="report-row indent">
            <span className="report-label">
              Solo código ejecutable <span className="rule-tag">OR-1</span>
            </span>
            {quality.is_clean_output
              ? <span className="stat-ok">✓ Sin texto/markdown mezclado</span>
              : <span className="stat-warn">⚠ Hay restos de markdown o texto</span>
            }
          </div>

          <div className="report-row indent">
            <span className="report-label">
              Empieza con <code>import pytest</code> <span className="rule-tag">OR-2</span>
            </span>
            {quality.starts_with_import_pytest
              ? <span className="stat-ok">✓ Cumple</span>
              : <span className="stat-warn">⚠ No cumple</span>
            }
          </div>

          <div className="report-row indent">
            <span className="report-label">
              Clase {quality.expected_class_name ? <code>{quality.expected_class_name}</code> : 'Test<Módulo>'} única <span className="rule-tag">OR-3</span>
            </span>
            {quality.has_expected_test_class
              ? <span className="stat-ok">✓ Presente</span>
              : <span className="stat-warn">⚠ Ausente o incorrecta</span>
            }
          </div>

          <div className="report-row indent">
            <span className="report-label">
              Given/When/Then <span className="rule-tag">OR-5</span>
            </span>
            {quality.has_given_when_then
              ? <span className="stat-ok">✓ Presente</span>
              : <span className="stat-warn">⚠ Ausente</span>
            }
          </div>

          <div className="report-row indent">
            <span className="report-label">Test smells</span>
            {quality.smells_detected.length === 0
              ? <span className="stat-ok">✓ Ninguno detectado</span>
              : (
                <div className="smell-list">
                  {quality.smells_detected.map(smell => (
                    <span key={smell} className="quality-smell">
                      ⚠ {SMELL_LABELS[smell] ?? smell}
                    </span>
                  ))}
                </div>
              )
            }
          </div>
        </>
      )}

    </div>
  )
}

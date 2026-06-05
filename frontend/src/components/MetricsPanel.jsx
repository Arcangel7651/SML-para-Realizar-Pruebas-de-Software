import './MetricsPanel.css'

function rateColor(rate) {
  if (rate >= 80) return 'good'
  if (rate >= 50) return 'warn'
  return 'bad'
}

const SMELL_LABELS = {
  assertion_roulette: 'assertion_roulette',
  empty_test:         'empty_test',
  generic_name:       'generic_name',
}

export default function MetricsPanel({ result, onCopy }) {
  const { compiles, compile_error, functions_found = [], metrics, quality } = result

  const hasDetails =
    (metrics && (metrics.tests_failed > 0 || metrics.tests_skipped > 0)) ||
    compile_error

  return (
    <div className="metrics-panel">
      <div className="metrics-header">
        <span className="metrics-title">TESTS GENERADOS</span>
        <button className="copy-btn" onClick={onCopy} title="Copiar código">
          Copiar
        </button>
      </div>

      {functions_found.length > 0 && (
        <div className="metrics-row">
          <span className="metrics-label">Funciones:</span>
          <div className="chip-list">
            {functions_found.map(fn => (
              <span key={fn} className="chip">{fn}</span>
            ))}
          </div>
        </div>
      )}

      <div className="metrics-row badges-row">
        <span className={`badge ${compiles ? 'badge-good' : 'badge-bad'}`}>
          {compiles ? '✓ Compila' : '✗ Error de sintaxis'}
        </span>

        {metrics && (
          <>
            <span className={`badge badge-${rateColor(metrics.pass_rate)}`}>
              {metrics.tests_passed}/{metrics.tests_total} pasan
            </span>
            <span className={`badge badge-${rateColor(metrics.line_coverage)}`}>
              {metrics.line_coverage}% cobertura
            </span>
          </>
        )}
      </div>

      {hasDetails && (
        <details className="metrics-details">
          <summary className="metrics-details-summary">Ver detalle</summary>
          <div className="metrics-details-body">
            {metrics?.tests_failed > 0 && (
              <div className="detail-row bad">✗ {metrics.tests_failed} test(s) fallido(s)</div>
            )}
            {metrics?.tests_skipped > 0 && (
              <div className="detail-row warn">⚠ {metrics.tests_skipped} test(s) omitido(s)</div>
            )}
            {compile_error && (
              <div className="detail-row bad mono">{compile_error}</div>
            )}
          </div>
        </details>
      )}

      {quality && (
        <div className="quality-section">
          <span className="quality-title">Calidad</span>
          <div className="quality-row">
            {quality.has_given_when_then ? (
              <span className="quality-ok">✓ Given/When/Then</span>
            ) : (
              <span className="quality-warn">⚠ Sin estructura Given/When/Then</span>
            )}
          </div>
          <div className="quality-row">
            {quality.smells_detected.length === 0 ? (
              <span className="quality-ok">✓ Sin test smells detectados</span>
            ) : (
              quality.smells_detected.map(smell => (
                <span key={smell} className="quality-smell">
                  ⚠ {SMELL_LABELS[smell] ?? smell}
                </span>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

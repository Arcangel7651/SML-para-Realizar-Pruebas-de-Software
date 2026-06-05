import Editor from '@monaco-editor/react'
import MetricsPanel from './MetricsPanel'
import './TestOutput.css'

export default function TestOutput({ result, loading, streamingCode }) {
  function handleCopy() {
    if (result?.tests) {
      navigator.clipboard.writeText(result.tests)
    }
  }

  // Streaming: el modelo está escribiendo
  if (loading && streamingCode) {
    return (
      <div className="output-wrapper">
        <div className="streaming-header">
          <span className="streaming-dot" />
          Generando tests...
        </div>
        <div className="editor-wrapper">
          <Editor
            height="calc(100vh - 160px)"
            language="python"
            value={streamingCode}
            theme="vs-dark"
            options={{
              readOnly: true,
              fontSize: 13,
              fontFamily: "'Fira Code', Consolas, monospace",
              minimap: { enabled: false },
              scrollBeyondLastLine: true,
              wordWrap: 'on',
              lineNumbers: 'on',
              renderLineHighlight: 'none',
              padding: { top: 12, bottom: 12 },
            }}
          />
        </div>
      </div>
    )
  }

  // Cargando pero aún sin tokens (preparando RAG, AST, etc.)
  if (loading) {
    return (
      <div className="output-center">
        <div className="output-spinner" />
        <div className="output-loading-text">Preparando contexto...</div>
      </div>
    )
  }

  // Sin resultado aún
  if (!result) {
    return (
      <div className="output-center output-empty">
        <div className="output-empty-icon">🧪</div>
        <div className="output-empty-title">Sin resultados aún</div>
        <div className="output-empty-hint">
          Sube un archivo <code>.py</code> y presiona <strong>Generar tests</strong>
        </div>
      </div>
    )
  }

  // Resultado final
  return (
    <div className="output-wrapper">
      <MetricsPanel result={result} onCopy={handleCopy} />

      <div className="editor-wrapper">
        <Editor
          height="calc(100vh - 160px)"
          language="python"
          value={result.tests}
          theme="vs-dark"
          options={{
            readOnly: true,
            fontSize: 13,
            fontFamily: "'Fira Code', Consolas, monospace",
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            wordWrap: 'on',
            lineNumbers: 'on',
            renderLineHighlight: 'line',
            padding: { top: 12, bottom: 12 },
          }}
        />
      </div>

      {result.context_used?.length > 0 && (
        <details className="rag-section">
          <summary className="rag-summary">
            Contexto RAG utilizado ({result.context_used.length} fragmentos)
          </summary>
          <div className="rag-list">
            {result.context_used.map((fragment, i) => (
              <div key={i} className="rag-fragment">
                <span className="rag-index">#{i + 1}</span>
                {fragment}
              </div>
            ))}
          </div>
        </details>
      )}
    </div>
  )
}

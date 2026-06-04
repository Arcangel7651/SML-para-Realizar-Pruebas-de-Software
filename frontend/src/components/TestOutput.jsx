import Editor from '@monaco-editor/react'
import './TestOutput.css'

export default function TestOutput({ result, loading }) {
  if (loading) {
    return (
      <div className="output-center">
        <div className="output-spinner" />
        <div className="output-loading-text">Generando tests con el SLM...</div>
      </div>
    )
  }

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

  return (
    <div className="output-wrapper">
      {result.compiles ? (
        <div className="compile-badge compile-ok">
          ✓ Código válido — el test compila correctamente
        </div>
      ) : (
        <div className="compile-badge compile-error">
          ✗ Error de sintaxis: {result.compile_error}
        </div>
      )}

      <div className="editor-wrapper">
        <Editor
          height="100%"
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

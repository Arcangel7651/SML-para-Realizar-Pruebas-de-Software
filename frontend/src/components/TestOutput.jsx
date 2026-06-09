import { useEffect, useMemo, useState } from 'react'
import Editor from '@monaco-editor/react'
import MetricsPanel from './MetricsPanel'
import './TestOutput.css'

const TABS = [
  { id: 'code',        label: 'Código generado' },
  { id: 'metrics',     label: 'Métricas y calidad' },
  { id: 'rag',         label: 'Contexto RAG' },
  { id: 'explanation', label: 'Explicación del modelo' },
]

export default function TestOutput({ result, loading, streamingCode, fileName, retrying }) {
  const [activeTab, setActiveTab] = useState('code')

  useEffect(() => {
    if (result) setActiveTab('code')
  }, [result])

  const moduleName = fileName ? fileName.replace(/\.py$/, '') : 'modulo'

  const downloadUrl = useMemo(() => {
    if (!result?.tests) return ''
    const blob = new Blob([result.tests], { type: 'text/plain' })
    return URL.createObjectURL(blob)
  }, [result?.tests])

  useEffect(() => {
    return () => { if (downloadUrl) URL.revokeObjectURL(downloadUrl) }
  }, [downloadUrl])

  function handleCopy() {
    if (result?.tests) {
      navigator.clipboard.writeText(result.tests)
    }
  }

  if (loading) {
    if (retrying) {
      return (
        <div className="output-center">
          <div className="output-spinner" />
          <div className="output-loading-text">Compilación fallida — reintentando...</div>
        </div>
      )
    }
    if (streamingCode) {
      return (
        <div className="output-center">
          <div className="streaming-pulse">
            <span className="streaming-dot" />
            <span className="streaming-dot" />
            <span className="streaming-dot" />
          </div>
          <div className="output-loading-text">Generando código de prueba...</div>
          <div className="output-loading-hint">
            {streamingCode.length.toLocaleString()} caracteres recibidos hasta ahora
          </div>
        </div>
      )
    }
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

  const hasExplanation = !!result.explanation?.trim()
  const visibleTabs = TABS.filter(t => t.id !== 'explanation' || hasExplanation)

  return (
    <div className="output-wrapper">
      <div className="output-tabs">
        {visibleTabs.map(tab => (
          <button
            key={tab.id}
            className={`output-tab${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div className="output-tab-content">
        {activeTab === 'code' && (
          <div className="editor-wrapper">
            <div className="tab-toolbar">
              <button className="copy-btn" onClick={handleCopy}>Copiar código</button>
              {downloadUrl && (
                <a className="copy-btn" href={downloadUrl} download={`test_${moduleName}.py`}>
                  Descargar .py
                </a>
              )}
            </div>
            <Editor
              height="calc(100vh - 200px)"
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
        )}

        {activeTab === 'metrics' && (
          <div className="metrics-tab">
            <MetricsPanel result={result} />
          </div>
        )}

        {activeTab === 'rag' && (
          <div className="rag-panel">
            {result.context_used?.length > 0 ? (
              <div className="rag-list">
                {result.context_used.map((fragment, i) => (
                  <div key={i} className="rag-fragment">
                    <span className="rag-index">#{i + 1}</span>
                    {fragment}
                  </div>
                ))}
              </div>
            ) : (
              <div className="output-center">
                <div className="output-empty-hint">No se utilizó contexto RAG para esta generación.</div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'explanation' && (
          <div className="explanation-panel">
            <p className="explanation-text">{result.explanation}</p>
          </div>
        )}
      </div>
    </div>
  )
}

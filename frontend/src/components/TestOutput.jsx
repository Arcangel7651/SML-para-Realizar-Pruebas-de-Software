import { useEffect, useMemo, useState } from 'react'
import Editor from '@monaco-editor/react'
import MetricsPanel from './MetricsPanel'
import Icon from './Icon'
import './TestOutput.css'

const TABS = [
  { id: 'code',        label: 'Código generado',     icon: 'code' },
  { id: 'metrics',     label: 'Métricas y calidad',   icon: 'gauge' },
  { id: 'rag',         label: 'Contexto RAG',         icon: 'database' },
  { id: 'explanation', label: 'Explicación del modelo', icon: 'message' },
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
        <div className="gen-center">
          <div className="gen-pulse"><i></i><i></i><i></i></div>
          <div className="gen-load-title">Generando código de prueba...</div>
          <div className="gen-retry-chip"><Icon name="refresh" size={13} /> Compilación fallida — reintentando...</div>
        </div>
      )
    }
    if (streamingCode) {
      return (
        <div className="gen-center">
          <div className="gen-pulse"><i></i><i></i><i></i></div>
          <div className="gen-load-title">Generando código de prueba...</div>
          <div className="gen-load-bar"></div>
          <div className="gen-load-sub">
            <span className="mono">{streamingCode.length.toLocaleString()}</span> caracteres recibidos hasta ahora
          </div>
        </div>
      )
    }
    return (
      <div className="gen-center">
        <div className="gen-pulse"><i></i><i></i><i></i></div>
        <div className="gen-load-title">Preparando contexto...</div>
      </div>
    )
  }

  // Sin resultado aún
  if (!result) {
    return (
      <div className="gen-center">
        <div className="gen-empty-icon"><Icon name="flask" size={38} /></div>
        <div className="gen-empty-title">Sin resultados aún</div>
        <div className="gen-empty-hint">
          Sube un archivo <code>.py</code> y presiona <b>Generar tests</b>
        </div>
      </div>
    )
  }

  const hasExplanation = !!result.explanation?.trim()
  const ragCount = result.context_used?.length ?? 0
  const visibleTabs = TABS.filter(t => t.id !== 'explanation' || hasExplanation)

  return (
    <div className="gen-result">
      <div className="gen-tabs">
        {visibleTabs.map(tab => (
          <button
            key={tab.id}
            className={`gen-tab${activeTab === tab.id ? ' active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <Icon name={tab.icon} size={15} />
            {tab.label}
            {tab.id === 'rag' && ragCount > 0 && <span className="badge">{ragCount}</span>}
          </button>
        ))}
      </div>

      <div className="gen-tab-content">
        {activeTab === 'code' && (
          <div className="gen-code-tab">
            <div className="gen-toolbar">
              <span className="file-pill"><Icon name="filecode" size={14} /> test_{moduleName}.py</span>
              <span className="spacer"></span>
              <button className="gen-tbtn" onClick={handleCopy}><Icon name="copy" size={14} /> Copiar código</button>
              {downloadUrl && (
                <a className="gen-tbtn primary" href={downloadUrl} download={`test_${moduleName}.py`}>
                  <Icon name="download" size={14} /> Descargar .py
                </a>
              )}
            </div>
            <div className="gen-editor">
              <Editor
                height="100%"
                language="python"
                value={result.tests}
                theme="vs-dark"
                options={{
                  readOnly: true,
                  fontSize: 13,
                  fontFamily: "'Geist Mono', 'Fira Code', Consolas, monospace",
                  minimap: { enabled: false },
                  scrollBeyondLastLine: false,
                  wordWrap: 'on',
                  lineNumbers: 'on',
                  renderLineHighlight: 'line',
                  padding: { top: 12, bottom: 12 },
                }}
              />
            </div>
          </div>
        )}

        {activeTab === 'metrics' && (
          <div className="gen-metrics">
            <MetricsPanel result={result} />
          </div>
        )}

        {activeTab === 'rag' && (
          <div className="gen-rag">
            {result.context_used?.length > 0 ? (
              <>
                <div className="gen-rag-head">
                  <span className="gen-rag-head-ic"><Icon name="database" size={18} /></span>
                  <div className="gen-rag-head-txt">
                    <b>Contexto recuperado del índice vectorial</b>
                    <span>Fragmentos inyectados al prompt</span>
                  </div>
                  <span className="pill">{ragCount} fragmento{ragCount === 1 ? '' : 's'}</span>
                </div>
                <div className="gen-rag-list">
                  {result.context_used.map((fragment, i) => (
                    <div key={i} className="gen-rag-frag">
                      <div className="gen-rag-frag-top">
                        <span className="gen-rag-index">{i + 1}</span>
                      </div>
                      <div className="gen-rag-code">{fragment}</div>
                    </div>
                  ))}
                </div>
              </>
            ) : (
              <div className="gen-center">
                <div className="gen-empty-hint">No se utilizó contexto RAG para esta generación.</div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'explanation' && (
          <div className="gen-expl">
            <div className="gen-expl-card">
              <div className="gen-expl-head">
                <span className="gen-expl-avatar"><Icon name="sparkles" size={19} /></span>
                <div className="gen-expl-head-txt">
                  <b>Cómo razonó el modelo</b>
                  <span>Resumen generado junto con la suite de pruebas</span>
                </div>
              </div>
              <div className="gen-expl-text">
                <p>{result.explanation}</p>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

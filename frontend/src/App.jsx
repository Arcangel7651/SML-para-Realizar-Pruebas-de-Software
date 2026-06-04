import { useState, useEffect } from 'react'
import axios from 'axios'
import './App.css'
import FileUpload from './components/FileUpload'
import PromptPanel from './components/PromptPanel'
import TestOutput from './components/TestOutput'

const PREFERRED = ['codellama', 'qwen', 'llama']

function pickDefaultModel(models) {
  for (const keyword of PREFERRED) {
    const found = models.find(m => m.toLowerCase().includes(keyword))
    if (found) return found
  }
  return models[0] ?? ''
}

export default function App() {
  const [file, setFile] = useState(null)
  const [fileName, setFileName] = useState('')
  const [prompt, setPrompt] = useState('Genera tests unitarios completos con pytest para este código.')
  const [model, setModel] = useState('')
  const [models, setModels] = useState([])
  const [ollamaStatus, setOllamaStatus] = useState('checking')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    axios.get('/api/health')
      .then(res => {
        const list = res.data.models ?? []
        setModels(list)
        setModel(pickDefaultModel(list))
        setOllamaStatus('ok')
      })
      .catch(() => setOllamaStatus('error'))
  }, [])

  function handleFileSelect(f) {
    setFile(f)
    setFileName(f.name)
    setResult(null)
    setError('')
  }

  async function handleGenerate() {
    if (!file || !model) return
    setLoading(true)
    setError('')
    setResult(null)

    const form = new FormData()
    form.append('file', file)
    form.append('prompt', prompt)
    form.append('model', model)

    try {
      const res = await axios.post('/api/generate-tests', form)
      setResult(res.data)
    } catch (err) {
      setError(err.response?.data?.detail ?? err.message ?? 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">
          <span>⚗</span> SLM Test Generator
        </div>
        <div className="header-subtitle">
          Basado en SMS sobre SLMs en pruebas de software
        </div>
        <div className="header-right">
          <select
            className="model-select"
            value={model}
            onChange={e => setModel(e.target.value)}
          >
            {models.length === 0 && (
              <option value="">Sin modelos disponibles</option>
            )}
            {models.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
          <div className="ollama-badge">
            <div className={`ollama-dot ${ollamaStatus}`} />
            {ollamaStatus === 'checking' ? 'Conectando...'
              : ollamaStatus === 'ok' ? 'Ollama OK'
              : 'Ollama offline'}
          </div>
        </div>
      </header>

      <main className="main">
        <div className="panel-left">
          <FileUpload onFileSelect={handleFileSelect} fileName={fileName} />
          <PromptPanel
            prompt={prompt}
            onChange={setPrompt}
            onGenerate={handleGenerate}
            disabled={!file || loading || !model}
            loading={loading}
          />
          {error && <div className="error-banner">{error}</div>}
        </div>

        <div className="panel-right">
          <TestOutput result={result} loading={loading} />
        </div>
      </main>
    </div>
  )
}

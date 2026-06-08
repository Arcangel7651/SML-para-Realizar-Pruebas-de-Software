import { useState, useEffect, useRef } from 'react'
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
  const [prompt, setPrompt] = useState('')
  const [model, setModel] = useState('')
  const [models, setModels] = useState([])
  const [ollamaStatus, setOllamaStatus] = useState('checking')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [streamingCode, setStreamingCode] = useState('')
  const [error, setError] = useState('')
  const [elapsed, setElapsed] = useState(0)

  const abortControllerRef = useRef(null)
  const timerRef = useRef(null)

  function startTimer() {
    setElapsed(0)
    const startedAt = Date.now()
    timerRef.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - startedAt) / 1000))
    }, 1000)
  }

  function stopTimer() {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }
  }

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
    setStreamingCode('')
    setError('')
  }

  async function handleGenerate() {
    if (!file || !model) return
    setLoading(true)
    setError('')
    setResult(null)
    setStreamingCode('')
    startTimer()

    const controller = new AbortController()
    abortControllerRef.current = controller

    const form = new FormData()
    form.append('file', file)
    form.append('prompt', prompt)
    form.append('model', model)
    form.append('run_pytest', true)

    try {
      const response = await fetch('/api/generate-tests-stream', {
        method: 'POST',
        body: form,
        signal: controller.signal,
      })

      if (!response.ok) {
        const text = await response.text()
        throw new Error(text || `HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let partialMeta = null
      let accumulated = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const lines = decoder.decode(value, { stream: true }).split('\n')
        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const msg = JSON.parse(line)
            if (msg.type === 'meta') {
              partialMeta = msg
            } else if (msg.type === 'token') {
              accumulated += msg.content
              setStreamingCode(accumulated)
            } else if (msg.type === 'done') {
              setResult({
                tests: msg.tests,
                explanation: msg.explanation,
                compiles: msg.compiles,
                compile_error: msg.compile_error,
                metrics: msg.metrics,
                quality: msg.quality,
                functions_found: partialMeta?.functions_found ?? [],
                context_used: partialMeta?.context_used ?? [],
              })
              setStreamingCode('')
            }
          } catch {
            // línea parcial, ignorar
          }
        }
      }
    } catch (err) {
      if (err.name === 'AbortError') {
        setError('Generación detenida por el usuario.')
      } else {
        setError(err.message ?? 'Error desconocido')
      }
    } finally {
      setLoading(false)
      stopTimer()
      abortControllerRef.current = null
    }
  }

  function handleStop() {
    abortControllerRef.current?.abort()
  }

  return (
    <div className="app">
      <header className="header">
        <div className="header-logo">
          <span>⚗</span> SLM Test Generator
        </div>
        <div className="header-subtitle">
          
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
            onStop={handleStop}
            disabled={!file || loading || !model}
            loading={loading}
            elapsed={elapsed}
          />
          {error && <div className="error-banner">{error}</div>}
        </div>

        <div className="panel-right">
          <TestOutput result={result} loading={loading} streamingCode={streamingCode} />
        </div>
      </main>
    </div>
  )
}

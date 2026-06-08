import { useEffect, useRef } from 'react'
import './PromptPanel.css'

function formatElapsed(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

export default function PromptPanel({ prompt, onChange, onGenerate, onStop, disabled, loading, elapsed = 0 }) {
  const textareaRef = useRef(null)

  useEffect(() => {
    function onKey(e) {
      if (e.ctrlKey && e.key === 'Enter' && !disabled) {
        onGenerate()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [disabled, onGenerate])

  return (
    <div className="prompt-panel">
      <label className="prompt-label">
        Instrucciones adicionales <span className="prompt-optional">(opcional)</span>
      </label>
      <textarea
        ref={textareaRef}
        className="prompt-textarea"
        value={prompt}
        onChange={e => onChange(e.target.value)}
        placeholder="Usa esto si quieres dar alguna instrucción adicional..."
        rows={5}
      />
      {loading ? (
        <div className="generating-controls">
          <div className="elapsed-timer">
            <span className="timer-dot" />
            {formatElapsed(elapsed)}
          </div>
          <button className="stop-btn" onClick={onStop}>
            Detener
          </button>
        </div>
      ) : (
        <button
          className="generate-btn"
          onClick={onGenerate}
          disabled={disabled}
        >
          Generar tests <kbd>Ctrl+↵</kbd>
        </button>
      )}
    </div>
  )
}

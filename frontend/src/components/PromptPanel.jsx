import { useEffect, useRef } from 'react'
import Icon from './Icon'
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
    <div className="gen-prompt">
      <label className="gen-label">
        Instrucciones <span className="opt">(opcional)</span>
      </label>
      <textarea
        ref={textareaRef}
        className="gen-textarea"
        value={prompt}
        onChange={e => onChange(e.target.value)}
        placeholder="Usa esto si quieres dar alguna instrucción adicional..."
        rows={5}
      />
      {loading ? (
        <div className="gen-running">
          <div className="gen-timer">
            <span className="live" />
            <Icon name="timer" size={15} />
            {formatElapsed(elapsed)}
          </div>
          <button className="gen-stop" onClick={onStop}>
            <Icon name="stop" size={13} /> Detener
          </button>
        </div>
      ) : (
        <button
          className="gen-btn"
          onClick={onGenerate}
          disabled={disabled}
        >
          <Icon name="sparkles" size={16} />
          <span>Generar tests</span>
          <kbd>Ctrl ↵</kbd>
        </button>
      )}
    </div>
  )
}

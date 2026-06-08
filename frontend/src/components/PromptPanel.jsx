import { useEffect, useRef } from 'react'
import './PromptPanel.css'

export default function PromptPanel({ prompt, onChange, onGenerate, disabled, loading, runPytest, onTogglePytest }) {
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
      <label className="toggle-label">
        <input
          type="checkbox"
          checked={runPytest}
          onChange={e => onTogglePytest(e.target.checked)}
          className="toggle-checkbox"
        />
        <span className="toggle-text">
          Evaluar con pytest
          <span className="toggle-hint">{runPytest ? '(+30-60s)' : '(más rápido)'}</span>
        </span>
      </label>
      <button
        className="generate-btn"
        onClick={onGenerate}
        disabled={disabled}
      >
        {loading ? (
          <span className="spinner" />
        ) : (
          <>Generar tests <kbd>Ctrl+↵</kbd></>
        )}
      </button>
    </div>
  )
}

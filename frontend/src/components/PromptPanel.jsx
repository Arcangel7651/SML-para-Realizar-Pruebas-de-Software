import { useEffect, useRef } from 'react'
import './PromptPanel.css'

export default function PromptPanel({ prompt, onChange, onGenerate, disabled, loading }) {
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
      <label className="prompt-label">Instrucciones adicionales</label>
      <textarea
        ref={textareaRef}
        className="prompt-textarea"
        value={prompt}
        onChange={e => onChange(e.target.value)}
        placeholder="Ej: Genera tests con casos límite y excepciones..."
        rows={5}
      />
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

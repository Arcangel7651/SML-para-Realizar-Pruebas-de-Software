import { useRef, useState } from 'react'
import Icon from './Icon'
import './FileUpload.css'

function formatSize(bytes) {
  if (!bytes && bytes !== 0) return ''
  if (bytes < 1024) return `${bytes} B`
  return `${(bytes / 1024).toFixed(1)} KB`
}

export default function FileUpload({ onFileSelect, fileName, file }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)

  function handleFile(f) {
    if (!f) return
    if (!f.name.endsWith('.py')) {
      alert('Solo se aceptan archivos .py')
      return
    }
    onFileSelect(f)
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files[0])
  }

  return (
    <div className="gen-upload">
      <div className="gen-eyebrow"><Icon name="filecode" size={13} /> Archivo fuente</div>
      <div
        className={`gen-drop ${dragging ? 'dragging' : ''} ${fileName ? 'loaded' : ''}`}
        onClick={() => inputRef.current.click()}
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".py"
          style={{ display: 'none' }}
          onChange={e => handleFile(e.target.files[0])}
        />
        {fileName ? (
          <div className="gen-file">
            <div className="gen-file-ic"><Icon name="filecode" size={20} /></div>
            <div className="gen-file-meta">
              <div className="gen-file-name">{fileName}</div>
              <div className="gen-file-sub">
                <span className="dot dot-good" /> {formatSize(file?.size)} · Python
              </div>
            </div>
            <span className="gen-file-change"><Icon name="swap" size={12} /> Cambiar</span>
          </div>
        ) : (
          <>
            <div className="gen-drop-icon"><Icon name="cloudup" size={24} /></div>
            <div className="gen-drop-title">Arrastra tu archivo <b>.py</b> aquí</div>
            <div className="gen-drop-hint">o haz clic para seleccionar</div>
          </>
        )}
      </div>
    </div>
  )
}

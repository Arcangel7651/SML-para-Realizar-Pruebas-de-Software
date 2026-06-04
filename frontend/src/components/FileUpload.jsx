import { useRef, useState } from 'react'
import './FileUpload.css'

export default function FileUpload({ onFileSelect, fileName }) {
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
    <div className="file-upload">
      <div
        className={`drop-zone ${dragging ? 'dragging' : ''} ${fileName ? 'has-file' : ''}`}
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
          <>
            <div className="file-icon">🐍</div>
            <div className="file-name">{fileName}</div>
            <div className="file-hint">Clic para cambiar archivo</div>
          </>
        ) : (
          <>
            <div className="upload-icon">📂</div>
            <div className="upload-label">Arrastra tu archivo <strong>.py</strong> aquí</div>
            <div className="upload-hint">o haz clic para seleccionar</div>
          </>
        )}
      </div>
    </div>
  )
}

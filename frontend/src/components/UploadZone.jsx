import { useCallback, useRef, useState } from 'react'

export default function UploadZone({ onFiles, busy, multiple = true }) {
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef(null)

  const handleFiles = useCallback(
    (fileList) => {
      const files = Array.from(fileList).filter((f) =>
        /\.(pdf|docx|txt)$/i.test(f.name)
      )
      if (files.length) onFiles(multiple ? files : [files[0]])
    },
    [onFiles, multiple]
  )

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault()
        setDragOver(true)
      }}
      onDragLeave={() => setDragOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDragOver(false)
        handleFiles(e.dataTransfer.files)
      }}
      onClick={() => !busy && inputRef.current?.click()}
      className={`relative rounded-lg border-2 border-dashed p-8 text-center cursor-pointer transition-colors
        ${dragOver ? 'border-amber bg-amber/5' : 'border-ink-600 hover:border-ink-600/80'}
        ${busy ? 'pointer-events-none opacity-60' : ''}`}
    >
      <input
        ref={inputRef}
        type="file"
        multiple={multiple}
        accept=".pdf,.docx,.txt"
        className="hidden"
        onChange={(e) => e.target.files.length && handleFiles(e.target.files)}
      />
      <svg
        className="mx-auto mb-3 text-ink-600"
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
      >
        <path
          d="M12 16V4m0 0 4 4m-4-4-4 4M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {busy ? (
        <p className="font-mono text-sm text-amber">Parsing &amp; scoring resumes…</p>
      ) : (
        <>
          <p className="text-sm text-paper-100">
            Drop resumes here, or <span className="text-amber">browse</span>
          </p>
          <p className="text-xs text-ink-600 mt-1">
            {multiple ? 'PDF, DOCX or TXT — single or bulk upload' : 'PDF, DOCX or TXT'}
          </p>
        </>
      )}
    </div>
  )
}

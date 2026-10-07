import { useRef, useState } from 'react'
import { detectIngredients } from '../api.js'
import { ACCEPTED_EXTENSIONS, ACCEPTED_TYPES, MAX_UPLOAD_MB } from '../ingredients.js'

function validate(file) {
  const name = file.name.toLowerCase()
  const extOk = ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
  if (!extOk || !ACCEPTED_TYPES.includes(file.type)) {
    return 'Please upload a .jpg, .jpeg or .png image.'
  }
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) {
    return `That image is over ${MAX_UPLOAD_MB} MB. Try a smaller one.`
  }
  return null
}

export default function Welcome({ onDetected, onManual }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [loading, setLoading] = useState(null) // object URL of the photo being scanned
  const [error, setError] = useState(null)

  async function handleFile(file) {
    if (!file) return
    const problem = validate(file)
    if (problem) {
      setError(problem)
      return
    }

    const url = URL.createObjectURL(file)
    setError(null)
    setLoading(url)
    try {
      const result = await detectIngredients(file)
      onDetected({ file, url }, result)
    } catch (e) {
      URL.revokeObjectURL(url)
      setError(e.message)
      setLoading(null)
    }
  }

  function onDrop(e) {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files?.[0])
  }

  return (
    <section className="welcome">
      <div className="welcome-inner">
        <p className="eyebrow eyebrow-light">NutriChef AI 👋</p>
        <h1 className="welcome-title">
          What's in your <em>kitchen</em> today?
        </h1>
        <p className="welcome-sub">
          Snap a photo of your ingredients and we'll turn them into recipes you can cook right now.
        </p>

        <div
          className={`dropzone ${dragging ? 'dragging' : ''} ${loading ? 'busy' : ''}`}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={onDrop}
        >
          {loading ? (
            <div className="scanning">
              <img src={loading} alt="Your upload" />
              <div className="scan-line" />
              <p>Scanning your ingredients…</p>
            </div>
          ) : (
            <>
              <div className="dropzone-icon" aria-hidden="true">
                <svg width="26" height="26" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <rect x="3" y="3" width="18" height="18" rx="3" />
                  <circle cx="8.5" cy="8.5" r="1.8" />
                  <path d="M21 15l-5-5L5 21" />
                </svg>
              </div>
              <p className="dropzone-title">Scan your ingredients</p>
              <p className="dropzone-hint">Drop a photo here, or browse — JPG or PNG</p>
              <button className="btn btn-sage" onClick={() => inputRef.current?.click()}>
                Upload photo
              </button>
            </>
          )}
          <input
            ref={inputRef}
            type="file"
            accept=".jpg,.jpeg,.png,image/jpeg,image/png"
            hidden
            onChange={(e) => {
              handleFile(e.target.files?.[0])
              e.target.value = ''
            }}
          />
        </div>

        {error && <p className="alert alert-dark">{error}</p>}

        <div className="tips">
          <p className="tips-title">For the best results</p>
          <div className="tip">
            <span aria-hidden="true">🥕</span>
            <p>
              <strong>Fruits &amp; vegetables:</strong> loose is fine — spread them out so each one is
              visible.
            </p>
          </div>
          <div className="tip">
            <span aria-hidden="true">🥫</span>
            <p>
              <strong>Pantry &amp; dairy</strong> (milk, coffee, pasta, rice, cereal, yogurt…): photograph
              them <strong>in their packaging</strong>. Milk in a glass won't be recognised.
            </p>
          </div>
          <div className="tip">
            <span aria-hidden="true">✍️</span>
            <p>
              <strong>Eggs, meat, fish, spices</strong> can't be detected yet — you can add them by
              name on the next screen.
            </p>
          </div>
        </div>

        <div className="divider"><span>or</span></div>

        <button className="btn btn-ghost-light" onClick={onManual} disabled={!!loading}>
          + Add ingredients manually
        </button>
      </div>
    </section>
  )
}

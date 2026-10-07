import { useState } from 'react'
import { emojiFor, normalise } from '../ingredients.js'

function PhotoWithBoxes({ url, detections }) {
  const [size, setSize] = useState(null)
  const [showBoxes, setShowBoxes] = useState(true)

  return (
    <div className="photo-wrap">
      <div className="photo">
        <img
          src={url}
          alt="Your uploaded ingredients"
          onLoad={(e) => setSize({ w: e.target.naturalWidth, h: e.target.naturalHeight })}
        />
        {showBoxes && size &&
          detections.map((d, i) => {
            const [x1, y1, x2, y2] = d.bbox
            return (
              <div
                key={i}
                className="box"
                style={{
                  left: `${(x1 / size.w) * 100}%`,
                  top: `${(y1 / size.h) * 100}%`,
                  width: `${((x2 - x1) / size.w) * 100}%`,
                  height: `${((y2 - y1) / size.h) * 100}%`,
                }}
              >
                <span>
                  {d.class_name} {Math.round(d.confidence * 100)}%
                </span>
              </div>
            )
          })}
      </div>
      {detections.length > 0 && (
        <button className="link-btn" onClick={() => setShowBoxes((s) => !s)}>
          {showBoxes ? 'Hide' : 'Show'} detection boxes
        </button>
      )}
    </div>
  )
}

export default function Ingredients({
  photo,
  detection,
  ingredients,
  setIngredients,
  prefs,
  setPrefs,
  suggestions,
  searching,
  error,
  onBack,
  onSubmit,
}) {
  const [draft, setDraft] = useState('')

  const detected = ingredients.filter((i) => i.source === 'detected')
  const manual = ingredients.filter((i) => i.source === 'manual')
  const selectedCount = ingredients.filter((i) => i.selected).length
  const have = new Set(ingredients.map((i) => normalise(i.name)))
  const oftenMissed = suggestions.often_missed.filter((s) => !have.has(s))

  function add(name) {
    const clean = normalise(name)
    if (!clean || have.has(clean)) {
      setDraft('')
      return
    }
    setIngredients([...ingredients, { name: clean, source: 'manual', selected: true }])
    setDraft('')
  }

  function toggle(name) {
    setIngredients(ingredients.map((i) => (i.name === name ? { ...i, selected: !i.selected } : i)))
  }

  function remove(name) {
    setIngredients(ingredients.filter((i) => i.name !== name))
  }

  return (
    <section className="screen">
      <header className="topbar">
        <button className="icon-btn" onClick={onBack} aria-label="Back">
          ‹
        </button>
        <span className="topbar-step">Step 1 of 2</span>
      </header>

      {photo ? (
        <span className="pill pill-sage">
          ✓ {detected.length} {detected.length === 1 ? 'ingredient' : 'ingredients'} detected
        </span>
      ) : (
        <span className="pill pill-sage">Manual entry</span>
      )}
      <h1 className="title">Your Ingredients</h1>
      <p className="subtitle">
        {photo
          ? 'Review what we found — tap an item to leave it out — then add anything we missed.'
          : 'Add what you have, and we\'ll find recipes that use it.'}
      </p>

      {photo && detection && <PhotoWithBoxes url={photo.url} detections={detection.detections} />}

      {photo && (
        <>
          <p className="section-label">Detected from photo</p>
          {detected.length ? (
            <div className="ingredient-grid">
              {detected.map((item) => (
                <button
                  key={item.name}
                  className={`ingredient-card ${item.selected ? '' : 'off'}`}
                  onClick={() => toggle(item.name)}
                  aria-pressed={item.selected}
                >
                  <span className="ingredient-emoji" aria-hidden="true">
                    {emojiFor(item.name)}
                  </span>
                  <span className="ingredient-text">
                    <span className="ingredient-name">{item.name}</span>
                    <span className="ingredient-meta">
                      {item.count > 1 ? `${item.count} found · ` : ''}
                      {Math.round(item.confidence * 100)}% sure
                    </span>
                  </span>
                  <span className="check" aria-hidden="true">
                    {item.selected ? '✓' : ''}
                  </span>
                </button>
              ))}
            </div>
          ) : (
            <p className="alert alert-warm">
              We couldn't recognise any ingredients in this photo. Try a clearer, closer shot with
              items spread out — or add them by name below.
            </p>
          )}

          {detection?.skipped?.length > 0 && (
            <p className="alert alert-warm">
              We also spotted <strong>{detection.skipped.join(', ')}</strong>, but that's too general to
              search for. Add the specific item below (e.g. "chili powder", "soy sauce").
            </p>
          )}
        </>
      )}

      <p className="section-label">{photo ? 'Add anything we missed' : 'Add ingredients'}</p>
      <form
        className="add-row"
        onSubmit={(e) => {
          e.preventDefault()
          add(draft)
        }}
      >
        <input
          className="text-input"
          list="ingredient-suggestions"
          placeholder="e.g. eggs, chili powder, chicken"
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          aria-label="Ingredient name"
        />
        <datalist id="ingredient-suggestions">
          {suggestions.ingredients.filter((s) => !have.has(s)).map((s) => (
            <option key={s} value={s} />
          ))}
        </datalist>
        <button className="btn btn-dark" type="submit" disabled={!draft.trim()}>
          Add
        </button>
      </form>

      {manual.length > 0 && (
        <div className="chips">
          {manual.map((item) => (
            <span key={item.name} className="chip chip-solid">
              {emojiFor(item.name)} {item.name}
              <button onClick={() => remove(item.name)} aria-label={`Remove ${item.name}`}>
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      {oftenMissed.length > 0 && (
        <>
          <p className="hint">Often missed — tap to add:</p>
          <div className="chips">
            {oftenMissed.map((s) => (
              <button key={s} className="chip" onClick={() => add(s)}>
                + {s}
              </button>
            ))}
          </div>
        </>
      )}

      <p className="section-label">Preferences</p>
      <div className="segmented" role="radiogroup" aria-label="Recipe ranking">
        <button
          role="radio"
          aria-checked={prefs.ranking === 1}
          className={prefs.ranking === 1 ? 'active' : ''}
          onClick={() => setPrefs({ ...prefs, ranking: 1 })}
        >
          Use most of my ingredients
        </button>
        <button
          role="radio"
          aria-checked={prefs.ranking === 2}
          className={prefs.ranking === 2 ? 'active' : ''}
          onClick={() => setPrefs({ ...prefs, ranking: 2 })}
        >
          Fewest missing items
        </button>
      </div>
      <label className="toggle">
        <input
          type="checkbox"
          checked={prefs.ignorePantry}
          onChange={(e) => setPrefs({ ...prefs, ignorePantry: e.target.checked })}
        />
        <span>Assume I have pantry basics (salt, water, flour…)</span>
      </label>

      {error && <p className="alert alert-error">{error}</p>}

      <div className="sticky-cta">
        <button
          className="btn btn-forest btn-block"
          onClick={onSubmit}
          disabled={!selectedCount || searching}
        >
          {searching
            ? 'Finding recipes…'
            : selectedCount
              ? `Find recipes with ${selectedCount} ${selectedCount === 1 ? 'ingredient' : 'ingredients'} →`
              : 'Add at least one ingredient'}
        </button>
      </div>
    </section>
  )
}

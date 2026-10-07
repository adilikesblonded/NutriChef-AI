import { useState } from 'react'
import { matchPercent } from '../ingredients.js'

const FILTERS = [
  { key: 'all', label: 'All', test: () => true },
  { key: 'ready', label: '✅ Nothing missing', test: (r) => r.missed_ingredients.length === 0 },
  { key: 'few', label: '🛒 Missing 2 or fewer', test: (r) => r.missed_ingredients.length <= 2 },
]

export default function RecipeList({ recipes, onBack, onOpen }) {
  const [filter, setFilter] = useState('all')
  const visible = recipes.filter(FILTERS.find((f) => f.key === filter).test)

  return (
    <section className="screen screen-wide">
      <header className="topbar">
        <button className="icon-btn" onClick={onBack} aria-label="Back to ingredients">
          ‹
        </button>
        <span className="topbar-step">Step 2 of 2</span>
      </header>

      <span className="pill pill-sage">
        {recipes.length} {recipes.length === 1 ? 'recipe' : 'recipes'} matched
      </span>
      <h1 className="title">Recipes For You</h1>
      <p className="subtitle">Sorted by how well they match your ingredients.</p>

      {recipes.length > 0 && (
        <div className="filters">
          {FILTERS.map((f) => (
            <button
              key={f.key}
              className={`filter ${filter === f.key ? 'active' : ''}`}
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}

      {recipes.length === 0 && (
        <p className="alert alert-warm">
          No recipes found for these ingredients. Go back and try adding a few more, or switch the
          preference to "Fewest missing items".
        </p>
      )}
      {recipes.length > 0 && visible.length === 0 && (
        <p className="alert alert-warm">No recipes match this filter — try "All".</p>
      )}

      <div className="recipe-grid">
        {visible.map((r) => {
          const match = matchPercent(r)
          return (
            <button key={r.id} className="recipe-card" onClick={() => onOpen(r)}>
              <div className="recipe-img">
                {r.image ? <img src={r.image} alt="" loading="lazy" /> : <span>🍽️</span>}
                <span className={`match ${match >= 75 ? 'match-high' : ''}`}>{match}% match</span>
              </div>
              <div className="recipe-body">
                <h2 className="recipe-title">{r.title}</h2>
                <p className="recipe-line">
                  <span className="dot dot-have" /> <strong>You have:</strong>{' '}
                  {r.used_ingredients.join(', ') || '—'}
                </p>
                <p className="recipe-line">
                  <span className="dot dot-miss" /> <strong>Missing:</strong>{' '}
                  {r.missed_ingredients.length ? r.missed_ingredients.join(', ') : 'nothing 🎉'}
                </p>
              </div>
            </button>
          )
        })}
      </div>
    </section>
  )
}

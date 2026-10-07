import { useEffect, useState } from 'react'
import { getRecipe } from '../api.js'
import { matchPercent, normalise } from '../ingredients.js'

const DAILY_KCAL = 2000

function htmlToText(html) {
  if (!html) return ''
  return new DOMParser().parseFromString(html, 'text/html').body.textContent || ''
}

function nutrient(recipe, name) {
  return recipe?.nutrition?.nutrients?.find((n) => n.name === name)
}

function NutritionPanel({ recipe }) {
  const kcal = nutrient(recipe, 'Calories')
  if (!kcal) return null

  const macros = [
    { label: 'Protein', n: nutrient(recipe, 'Protein'), cls: 'protein' },
    { label: 'Carbs', n: nutrient(recipe, 'Carbohydrates'), cls: 'carbs' },
    { label: 'Fat', n: nutrient(recipe, 'Fat'), cls: 'fat' },
  ]
  const share = Math.min(kcal.amount / DAILY_KCAL, 1)
  const r = 34
  const circumference = 2 * Math.PI * r

  return (
    <div className="nutrition">
      <p className="nutrition-title">🔥 Nutrition · per serving</p>
      <div className="nutrition-top">
        <div className="ring">
          <svg viewBox="0 0 80 80" width="96" height="96" aria-hidden="true">
            <circle cx="40" cy="40" r={r} className="ring-track" />
            <circle
              cx="40"
              cy="40"
              r={r}
              className="ring-fill"
              strokeDasharray={`${share * circumference} ${circumference}`}
              transform="rotate(-90 40 40)"
            />
          </svg>
          <div className="ring-label">
            <strong>{Math.round(kcal.amount)}</strong>
            <span>kcal</span>
          </div>
        </div>
        <div className="bars">
          {macros.map(({ label, n, cls }) =>
            n ? (
              <div key={label} className="bar-row">
                <span>{label}</span>
                <div className="bar">
                  <div
                    className={`bar-fill ${cls}`}
                    style={{ width: `${Math.min(n.percentOfDailyNeeds ?? 0, 100)}%` }}
                  />
                </div>
                <span className="bar-pct">{Math.round(n.percentOfDailyNeeds ?? 0)}%</span>
              </div>
            ) : null,
          )}
          <p className="bars-note">
            {Math.round(share * 100)}% of a {DAILY_KCAL.toLocaleString()} kcal day · bars show % of
            daily needs
          </p>
        </div>
      </div>
      <div className="macros">
        {macros.map(({ label, n, cls }) =>
          n ? (
            <div key={label} className={`macro ${cls}`}>
              <strong>
                {Math.round(n.amount)}
                {n.unit}
              </strong>
              <span>{label}</span>
            </div>
          ) : null,
        )}
      </div>
    </div>
  )
}

export default function RecipeDetail({ summary, cache, userIngredients, ignorePantry, onBack }) {
  const [recipe, setRecipe] = useState(cache.get(summary.id) || null)
  const [error, setError] = useState(null)

  useEffect(() => {
    if (cache.has(summary.id)) return
    let cancelled = false
    getRecipe(summary.id)
      .then((data) => {
        cache.set(summary.id, data)
        if (!cancelled) setRecipe(data)
      })
      .catch((e) => !cancelled && setError(e.message))
    return () => {
      cancelled = true
    }
  }, [summary.id, cache])

  const usedIds = new Set(summary.used_ingredient_ids)
  const missedIds = new Set(summary.missed_ingredient_ids)
  const mine = userIngredients.map(normalise)

  // 'have' | 'need' | 'basic' (a pantry staple Spoonacular left out of both lists)
  function statusOf(ing) {
    if (usedIds.has(ing.id)) return 'have'
    if (missedIds.has(ing.id)) return 'need'
    const name = normalise(ing.name || '')
    if (name && mine.some((m) => name.includes(m) || m.includes(name))) return 'have'
    return ignorePantry ? 'basic' : 'need'
  }

  // Spoonacular sometimes repeats an ingredient line
  const lines = []
  const seen = new Set()
  for (const ing of recipe?.extendedIngredients || []) {
    const key = `${ing.id}|${ing.original}`
    if (!seen.has(key)) {
      seen.add(key)
      lines.push(ing)
    }
  }
  const haveCount = lines.filter((ing) => statusOf(ing) === 'have').length
  const needCount = lines.filter((ing) => statusOf(ing) === 'need').length

  const steps = recipe?.analyzedInstructions?.[0]?.steps || []
  const plainInstructions = htmlToText(recipe?.instructions)

  return (
    <section className="screen detail">
      <div className="hero">
        {summary.image || recipe?.image ? (
          <img src={recipe?.image || summary.image} alt="" />
        ) : (
          <span className="hero-fallback">🍽️</span>
        )}
        <button className="icon-btn hero-back" onClick={onBack} aria-label="Back to recipes">
          ‹
        </button>
      </div>

      <div className="detail-head">
        <h1 className="title">{summary.title}</h1>
        <span className="pill pill-sage">{matchPercent(summary)}% match</span>
      </div>

      {recipe && (
        <p className="meta">
          {recipe.readyInMinutes ? <span>⏱ {recipe.readyInMinutes} min</span> : null}
          {recipe.servings ? <span>👤 {recipe.servings} servings</span> : null}
          {recipe.vegetarian ? <span>🌱 Vegetarian</span> : null}
          {recipe.vegan ? <span>🌿 Vegan</span> : null}
          {recipe.glutenFree ? <span>🌾 Gluten-free</span> : null}
          {recipe.dairyFree ? <span>🥛 Dairy-free</span> : null}
        </p>
      )}

      {error && <p className="alert alert-error">{error}</p>}
      {!recipe && !error && <div className="skeleton" aria-label="Loading recipe" />}

      {recipe && (
        <>
          <NutritionPanel recipe={recipe} />

          <div className="section-row">
            <p className="section-label">Ingredients</p>
            <span className="section-note">
              {haveCount} have · {needCount} to buy
            </span>
          </div>
          <ul className="ing-list">
            {lines.map((ing) => {
              const status = statusOf(ing)
              return (
                <li key={`${ing.id}|${ing.original}`} className={status}>
                  <span className={`dot dot-${status}`} />
                  <span className="ing-text">{ing.original}</span>
                  <span className="ing-tag">{status === 'basic' ? 'pantry' : status}</span>
                </li>
              )
            })}
          </ul>

          <p className="section-label">Method</p>
          {steps.length > 0 ? (
            <ol className="steps">
              {steps.map((s) => (
                <li key={s.number}>{s.step}</li>
              ))}
            </ol>
          ) : plainInstructions ? (
            <p className="instructions">{plainInstructions}</p>
          ) : (
            <p className="hint">No written steps for this recipe — see the original below.</p>
          )}

          {recipe.sourceUrl && (
            <a className="btn btn-terracotta btn-block" href={recipe.sourceUrl} target="_blank" rel="noreferrer">
              View original recipe ↗
            </a>
          )}
        </>
      )}
    </section>
  )
}

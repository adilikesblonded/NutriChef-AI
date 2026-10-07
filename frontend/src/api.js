// All calls go through Vite's /api proxy to the FastAPI backend.
const BASE = '/api'

const BACKEND_DOWN =
  "Can't reach the backend. Start it with: python -m uvicorn backend.main:app --reload"

async function request(path, options) {
  let res
  try {
    res = await fetch(BASE + path, options)
  } catch {
    throw new Error(BACKEND_DOWN)
  }

  let body = null
  try {
    body = await res.json()
  } catch {
    // Vite's proxy answers with an empty 5xx when the backend is not running
    if (!res.ok) throw new Error(BACKEND_DOWN)
  }

  if (!res.ok) {
    if (res.status === 429) {
      throw new Error(
        "Spoonacular's daily limit has been used up. Try again tomorrow — searches you already ran today still work.",
      )
    }
    const detail = body?.detail
    throw new Error(typeof detail === 'string' ? detail : `Request failed (${res.status})`)
  }
  return body
}

export function getSuggestions() {
  return request('/suggestions')
}

export function detectIngredients(file, minConfidence = 0.4) {
  const form = new FormData()
  form.append('image', file)
  return request(`/detect?min_confidence=${minConfidence}`, { method: 'POST', body: form })
}

export function searchRecipes({ ingredients, ranking, ignorePantry, number = 12 }) {
  return request('/recipes', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ingredients, ranking, ignore_pantry: ignorePantry, number }),
  })
}

export function getRecipe(id) {
  return request(`/recipes/${id}`)
}

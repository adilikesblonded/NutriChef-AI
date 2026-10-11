// In production VITE_API_URL points at the deployed backend (e.g. on Render).
// In development it is unset and calls go through Vite's /api proxy.
const BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/+$/, '')

const BACKEND_DOWN = import.meta.env.VITE_API_URL
  ? "Can't reach the server. It may be waking up after being idle — please try again in a minute."
  : "Can't reach the backend. Start it with: python -m uvicorn backend.main:app --reload"

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

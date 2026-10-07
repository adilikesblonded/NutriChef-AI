import { useEffect, useRef, useState } from 'react'
import { getSuggestions, searchRecipes } from './api.js'
import { ingredientsFromDetection } from './ingredients.js'
import Welcome from './screens/Welcome.jsx'
import Ingredients from './screens/Ingredients.jsx'
import RecipeList from './screens/RecipeList.jsx'
import RecipeDetail from './screens/RecipeDetail.jsx'

export default function App() {
  const [screen, setScreen] = useState('welcome')

  // { file, url } of the uploaded photo, and the raw /detect response
  const [photo, setPhoto] = useState(null)
  const [detection, setDetection] = useState(null)

  // [{ name, source: 'detected' | 'manual', selected, count, confidence, classes }]
  const [ingredients, setIngredients] = useState([])
  const [prefs, setPrefs] = useState({ ranking: 1, ignorePantry: true })

  const [recipes, setRecipes] = useState([])
  const [searching, setSearching] = useState(false)
  const [searchError, setSearchError] = useState(null)
  const [activeRecipe, setActiveRecipe] = useState(null)

  // Recipe details already fetched this session (each fetch costs quota)
  const detailCache = useRef(new Map())

  // Autocomplete names and one-tap chips, loaded once from the backend
  const [suggestions, setSuggestions] = useState({ ingredients: [], often_missed: [] })

  useEffect(() => {
    getSuggestions()
      .then(setSuggestions)
      .catch(() => {}) // manual entry still works without suggestions
  }, [])

  useEffect(() => {
    window.scrollTo(0, 0)
  }, [screen])

  function handleDetected(newPhoto, result) {
    if (photo) URL.revokeObjectURL(photo.url)
    setPhoto(newPhoto)
    setDetection(result)
    setIngredients(ingredientsFromDetection(result))
    setSearchError(null)
    setScreen('ingredients')
  }

  function handleManual() {
    if (photo) URL.revokeObjectURL(photo.url)
    setPhoto(null)
    setDetection(null)
    setIngredients([])
    setSearchError(null)
    setScreen('ingredients')
  }

  async function handleFindRecipes() {
    const selected = ingredients.filter((i) => i.selected).map((i) => i.name)
    if (!selected.length) return

    setSearching(true)
    setSearchError(null)
    try {
      const result = await searchRecipes({
        ingredients: selected,
        ranking: prefs.ranking,
        ignorePantry: prefs.ignorePantry,
      })
      setRecipes(result.recipes)
      setScreen('recipes')
    } catch (e) {
      setSearchError(e.message)
    } finally {
      setSearching(false)
    }
  }

  function openRecipe(recipe) {
    setActiveRecipe(recipe)
    setScreen('detail')
  }

  return (
    <div className="app">
      {screen === 'welcome' && (
        <Welcome onDetected={handleDetected} onManual={handleManual} />
      )}

      {screen === 'ingredients' && (
        <Ingredients
          photo={photo}
          detection={detection}
          ingredients={ingredients}
          setIngredients={setIngredients}
          prefs={prefs}
          setPrefs={setPrefs}
          suggestions={suggestions}
          searching={searching}
          error={searchError}
          onBack={() => setScreen('welcome')}
          onSubmit={handleFindRecipes}
        />
      )}

      {screen === 'recipes' && (
        <RecipeList
          recipes={recipes}
          onBack={() => setScreen('ingredients')}
          onOpen={openRecipe}
        />
      )}

      {screen === 'detail' && activeRecipe && (
        <RecipeDetail
          summary={activeRecipe}
          cache={detailCache.current}
          userIngredients={ingredients.filter((i) => i.selected).map((i) => i.name)}
          ignorePantry={prefs.ignorePantry}
          onBack={() => setScreen('recipes')}
        />
      )}

      <footer className="attribution">
        Recipe and nutrition data from{' '}
        <a href="https://spoonacular.com/food-api" target="_blank" rel="noreferrer">
          spoonacular
        </a>
      </footer>
    </div>
  )
}

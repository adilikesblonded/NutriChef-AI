// Upload rules, emoji for the ingredient cards, and helpers.
// Ingredient suggestions come from the backend's GET /suggestions.

export const ACCEPTED_EXTENSIONS = ['.jpg', '.jpeg', '.png']
export const ACCEPTED_TYPES = ['image/jpeg', 'image/png']
export const MAX_UPLOAD_MB = 10

const EMOJI = {
  almond: '🌰', apple: '🍎', apricot: '🍑', artichoke: '🌿', asparagus: '🌿',
  avocado: '🥑', banana: '🍌', 'bell pepper': '🫑', blackberr: '🫐', blueberr: '🫐',
  bread: '🍞', broccoli: '🥦', brussels: '🥬', cantaloupe: '🍈', carrot: '🥕',
  cauliflower: '🥦', celery: '🥬', cereal: '🥣', cheese: '🧀', cherr: '🍒',
  chickpea: '🫘', chili: '🌶️', coconut: '🥥', coffee: '☕', oil: '🫒', corn: '🌽',
  cucumber: '🥒', date: '🌴', eggplant: '🍆', fig: '🟣', garlic: '🧄', ginger: '🫚',
  grape: '🍇', 'green bean': '🫛', kiwi: '🥝', lemon: '🍋', lettuce: '🥬', lime: '🍋',
  melon: '🍈', milk: '🥛', mushroom: '🍄', nut: '🥜', onion: '🧅', orange: '🍊',
  papaya: '🥭', pasta: '🍝', pea: '🫛', peach: '🍑', pear: '🍐', persimmon: '🍅',
  pickle: '🥒', pineapple: '🍍', potato: '🥔', prune: '🟣', pumpkin: '🎃',
  radish: '🌱', raspberr: '🍓', 'red bell pepper': '🌶️', rice: '🍚',
  'spring onion': '🌱', strawberr: '🍓', 'sweet potato': '🍠', tea: '🍵', tofu: '🧈',
  tomato: '🍅', turnip: '🌱', watermelon: '🍉', yogurt: '🥛', zucchini: '🥒',
  egg: '🥚', butter: '🧈', chicken: '🍗', beef: '🥩', bacon: '🥓', fish: '🐟',
  salmon: '🐟', tuna: '🐟', shrimp: '🦐', flour: '🌾', sugar: '🍬', salt: '🧂',
  honey: '🍯', chocolate: '🍫', spinach: '🥬', bean: '🫘', sauce: '🥫',
}

export function emojiFor(name) {
  const key = name.toLowerCase()
  if (EMOJI[key]) return EMOJI[key]
  // longest matching fragment wins ("sweet potatoes" -> sweet potato, not potato)
  const match = Object.keys(EMOJI)
    .filter((k) => key.includes(k))
    .sort((a, b) => b.length - a.length)[0]
  return match ? EMOJI[match] : '🥗'
}

export function normalise(name) {
  return name.trim().toLowerCase().replace(/\s+/g, ' ')
}

// Turn a /detect response into editable ingredient entries
export function ingredientsFromDetection(result) {
  return result.ingredients.map((name) => {
    const classes = result.sources[name] || []
    const hits = result.detections.filter((d) => classes.includes(d.class_name.toLowerCase()))
    return {
      name,
      source: 'detected',
      classes,
      count: hits.length,
      confidence: hits.reduce((max, h) => Math.max(max, h.confidence), 0),
      selected: true,
    }
  })
}

export function matchPercent(recipe) {
  const used = recipe.used_ingredients.length
  const total = used + recipe.missed_ingredients.length
  return total ? Math.round((used / total) * 100) : 0
}

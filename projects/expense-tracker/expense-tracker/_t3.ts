// Variant C: arrow function closures
function initTagInput(): void {
  const list = document.getElementById('tagList')
  const suggestions = document.getElementById('tagSuggestions')
  if (!list || !suggestions) return
  const renderTags = (): void => {
    list.innerHTML = ''
  }
  const showSuggestions = (): void => {
    suggestions.hidden = true
  }
}
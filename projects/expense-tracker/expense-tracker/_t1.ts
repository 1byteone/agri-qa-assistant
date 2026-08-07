// Variant A: exact EntryForm pattern (|| chain + function declarations + DOM calls)
function initTagInput(): void {
  const input = document.getElementById('tagInput') as HTMLInputElement | null
  const list = document.getElementById('tagList')
  const suggestions = document.getElementById('tagSuggestions')
  if (!input || !list || !suggestions) return
  function renderTags(): void {
    list.innerHTML = ''
  }
  function showSuggestions(): void {
    suggestions.hidden = true
  }
}
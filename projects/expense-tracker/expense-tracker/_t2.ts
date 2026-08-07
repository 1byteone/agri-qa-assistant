// Variant B: simple guard, function declarations
function initTagInput(): void {
  const list = document.getElementById('tagList')
  if (!list) return
  function renderTags(): void {
    list.innerHTML = ''
  }
}
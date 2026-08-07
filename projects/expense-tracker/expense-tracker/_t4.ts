// Variant D: chip keydown listener (Event type check)
function init(): void {
  const chips = document.querySelectorAll('.chip')
  chips.forEach(chip => {
    chip.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') { e.preventDefault() }
    })
  })
}
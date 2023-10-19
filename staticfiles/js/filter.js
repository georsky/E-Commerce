// Filter for Categorys to work directly when u press one of the checkbox

// Get all checkboxes with the class "category-checkbox"
const checkboxes = document.querySelectorAll('.category-checkbox');

checkboxes.forEach(checkbox => {
  checkbox.addEventListener('change', filterProducts);
});

function filterProducts() {
  const selectedCategoryIds = Array.from(document.querySelectorAll('.category-checkbox:checked')).map(checkbox => checkbox.value);
  const productContainers = document.querySelectorAll('.prod-category');

  productContainers.forEach(container => {
    const productCategoryIds = container.getAttribute('data-categories').split(',');
    const isVisible = selectedCategoryIds.length === 0 || selectedCategoryIds.some(id => productCategoryIds.includes(id));

    if (isVisible) {
      container.style.display = 'block';
    } else {
      container.style.display = 'none';
    }
  });
}

// Initial filtering based on checked checkboxes
filterProducts();

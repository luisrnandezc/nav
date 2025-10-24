// Report Detail Page - Simplified Add/Delete Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get the report ID from the URL
    const pathParts = window.location.pathname.split('/').filter(part => part !== '');
    window.reportId = pathParts[pathParts.length - 1];
    
    // Initialize functionality
    initializeAddDelete();
    initializeDjangoForm();
});

// Add/Delete Functionality
function initializeAddDelete() {
    // Set up event delegation for add/delete buttons
    document.addEventListener('click', function(e) {
        const target = e.target;
        
        // Handle add buttons
        if (target.classList.contains('add-btn')) {
            e.preventDefault();
            e.stopPropagation();
            
            // Determine item type based on which section the button is in
            const riskSection = target.closest('.info-section').querySelector('.risk-analysis-list');
            const recommendationSection = target.closest('.info-section').querySelector('.recommendations-list');
            
            if (riskSection) {
                addNewItem('risk');
            } else if (recommendationSection) {
                addNewItem('recommendation');
            }
        }
        
        // Handle delete buttons
        if (target.classList.contains('delete-btn')) {
            e.preventDefault();
            e.stopPropagation();
            
            const item = target.closest('.risk-item') || target.closest('.recommendation-item');
            if (item) {
                const index = parseInt(item.getAttribute('data-index'));
                const itemType = item.classList.contains('risk-item') ? 'risk' : 'recommendation';
                deleteItem(itemType, index);
            }
        }
    });
}

// Add new item
function addNewItem(itemType) {
    const containerClass = itemType === 'risk' ? 'risk-analysis-list' : 'recommendations-list';
    const container = document.querySelector(`.${containerClass}`);
    if (!container) {
        console.error(`Container not found: .${containerClass}`);
        return;
    }
    
    // Check if there's already an input form
    const existingForm = container.querySelector('.input-form');
    if (existingForm) {
        return; // Don't create another one
    }
    
    // Create a simple input form
    const inputForm = document.createElement('div');
    inputForm.className = `${itemType}-item input-form`;
    inputForm.innerHTML = `
        <div class="input-container">
            <textarea class="item-textarea" placeholder="Descripción del ${itemType === 'risk' ? 'riesgo' : 'recomendación'}..." rows="3"></textarea>
            <div class="input-controls">
                <select class="relevance-select">
                    <option value="high">Alta</option>
                    <option value="medium" selected>Media</option>
                    <option value="low">Baja</option>
                </select>
                <div class="input-buttons">
                    <button type="button" class="save-input-btn">Guardar</button>
                    <button type="button" class="cancel-input-btn">Cancelar</button>
                </div>
            </div>
        </div>
    `;
    
    // Add to container
    container.appendChild(inputForm);
    
    // Focus on textarea
    const textarea = inputForm.querySelector('.item-textarea');
    textarea.focus();
    
    // Set up event listeners
    const saveBtn = inputForm.querySelector('.save-input-btn');
    const cancelBtn = inputForm.querySelector('.cancel-input-btn');
    
    saveBtn.addEventListener('click', () => saveNewItem(itemType, inputForm));
    cancelBtn.addEventListener('click', () => inputForm.remove());
}

function saveNewItem(itemType, inputForm) {
    const textarea = inputForm.querySelector('.item-textarea');
    const select = inputForm.querySelector('.relevance-select');
    
    const text = textarea.value.trim();
    const relevance = select.value;
    
    if (!text) {
        alert(`Por favor ingrese una descripción del ${itemType === 'risk' ? 'riesgo' : 'recomendación'}.`);
        return;
    }
    
    const data = {
        text: text,
        relevance: relevance
    };
    
    const url = `/sms/report/${window.reportId}/${itemType}/add/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify(data)
    })
    .then(response => response.text())
    .then(text => {
        try {
            const result = JSON.parse(text);
            if (result.success) {
                // Remove the input form
                inputForm.remove();
                // Add the actual item
                addItemToDOM(itemType, result.new_index, data.text, data.relevance);
            } else {
                alert('Error: ' + result.message);
            }
        } catch (parseError) {
            console.error('JSON parse error:', parseError);
            alert('Error: Invalid response from server');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error al agregar el ${itemType === 'risk' ? 'riesgo' : 'recomendación'}`);
    });
}

// Add item to DOM
function addItemToDOM(itemType, newIndex, text, relevance) {
    const containerClass = itemType === 'risk' ? 'risk-analysis-list' : 'recommendations-list';
    const container = document.querySelector(`.${containerClass}`);
    if (!container) {
        console.error(`Container not found: .${containerClass}`);
        return;
    }
    
    const relevanceText = relevance === 'high' ? 'Alta' : relevance === 'medium' ? 'Media' : 'Baja';
    
    // Create the new item HTML
    const itemHTML = `
        <div class="${itemType}-item relevance-${relevance}" data-index="${newIndex}">
            <div class="${itemType}-relevance">
                <span class="relevance-badge ${relevance}">${relevanceText}</span>
            </div>
            <div class="${itemType}-text">
                ${text}
            </div>
            <button type="button" class="delete-btn" title="Eliminar ${itemType === 'risk' ? 'riesgo' : 'recomendación'}">×</button>
        </div>
    `;
    
    // Add the new item to the container
    container.insertAdjacentHTML('beforeend', itemHTML);
}

// Delete item
function deleteItem(itemType, index) {
    const itemName = itemType === 'risk' ? 'riesgo' : 'recomendación';
    if (!confirm(`¿Está seguro de que desea eliminar este ${itemName}?`)) {
        return;
    }
    
    const url = `/sms/report/${window.reportId}/${itemType}/${index}/delete/`;
    
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(result => {
        if (result.success) {
            // Remove the item from DOM
            const item = document.querySelector(`.${itemType}-item[data-index="${index}"]`);
            item.remove();
            
            // Update indices for remaining items
            updateItemIndices(itemType);
        } else {
            alert('Error: ' + result.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Error al eliminar el ${itemName}`);
    });
}

function updateItemIndices(itemType) {
    const containerClass = itemType === 'risk' ? 'risk-analysis-list' : 'recommendations-list';
    const container = document.querySelector(`.${containerClass}`);
    if (!container) return;
    
    const items = container.querySelectorAll(`.${itemType}-item:not(.input-form)`);
    items.forEach((item, newIndex) => {
        item.setAttribute('data-index', newIndex);
    });
}
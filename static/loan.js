document.addEventListener('DOMContentLoaded', () => {
    const devicesTable = document.getElementById('devices-table');
    const loanButton = document.getElementById('loan-button');
    const selectedDeviceIdInput = document.getElementById('selected_device_id');
    const filterButtonsContainer = document.getElementById('category-filters');
    
    let selectedRow = null;

    // --- 1. Row Selection Toggle Logic ---
    devicesTable.addEventListener('click', (event) => {
        const row = event.target.closest('.device-row');
        if (!row) return;

        const deviceId = row.getAttribute('data-device-id');

        if (row === selectedRow) {
            // Deselect the current row
            row.classList.remove('selected-row');
            selectedRow = null;
            selectedDeviceIdInput.value = '';
            loanButton.disabled = true;
        } else {
            // Deselect previous row if one exists
            if (selectedRow) {
                selectedRow.classList.remove('selected-row');
            }
            // Select new row
            row.classList.add('selected-row');
            selectedRow = row;
            selectedDeviceIdInput.value = deviceId;
            loanButton.disabled = false;
        }
    });

    // --- 2. Filter Button Logic ---
    filterButtonsContainer.addEventListener('click', (event) => {
        const button = event.target.closest('.filter-btn');
        if (!button) return;

        const selectedCategory = button.getAttribute('data-category');
        const allRows = devicesTable.querySelectorAll('.device-row');
        const allButtons = filterButtonsContainer.querySelectorAll('.filter-btn');

        // Reset previous selection and button styling
        if (selectedRow) {
            selectedRow.classList.remove('selected-row');
            selectedRow = null;
            selectedDeviceIdInput.value = '';
            loanButton.disabled = true;
        }
        
        allButtons.forEach(btn => btn.classList.remove('active-filter'));
        button.classList.add('active-filter');


        // Apply filter to table rows
        allRows.forEach(row => {
            const rowCategory = row.getAttribute('data-category');
            
            if (selectedCategory === 'All' || rowCategory === selectedCategory) {
                row.style.display = ''; // Show row
            } else {
                row.style.display = 'none'; // Hide row
            }
        });
    });

    // Initialize the "Show All" button as active on load
    const allButton = document.querySelector('[data-category="All"]');
    if(allButton) {
        allButton.classList.add('active-filter');
    }

    // Add CSS for selected row (needed since this is a separate file)
    const style = document.createElement('style');
    style.textContent = `
        .selected-row {
            background-color: #fce8d5 !important; /* Light orange for visual feedback */
            border: 2px solid #ff9800;
        }
        .active-filter {
            background-color: #00bcd4 !important; /* A different blue/cyan for active filter */
            transform: scale(1.05);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
    `;
    document.head.appendChild(style);
});
// This script handles the automatic generation of the device Rubric ID
// and confirmation for delete actions in the admin interface.
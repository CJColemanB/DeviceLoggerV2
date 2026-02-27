document.addEventListener('DOMContentLoaded', () => {
    const devicesTable = document.getElementById('devices-table');
    const loanButton = document.getElementById('loan-button');
    const selectedDeviceIdInput = document.getElementById('selected_device_ids');
    const filterButtonsContainer = document.getElementById('category-filters');
    const selectionCountLabel = document.getElementById('selection-count');
    
    // We now use an array to store multiple IDs
    let selectedDeviceIds = [];

    // --- Helper to update UI state ---
    const updateSelectionUI = () => {
        const count = selectedDeviceIds.length;
        
        // Update hidden input with comma-separated IDs
        selectedDeviceIdInput.value = selectedDeviceIds.join(',');
        
        // Update selection label
        selectionCountLabel.textContent = `(${count} selected)`;
        
        // Enable/Disable button
        loanButton.disabled = count === 0;
        
        // Change button text dynamically
        loanButton.textContent = count > 1 
            ? `Loan ${count} Selected Devices` 
            : (count === 1 ? 'Loan 1 Selected Device' : 'Select Devices to Loan');
    };

    // --- 1. Multi-Selection Logic ---
    devicesTable.addEventListener('click', (event) => {
        const row = event.target.closest('.device-row');
        if (!row) return;

        const deviceId = row.getAttribute('data-device-id');

        if (selectedDeviceIds.includes(deviceId)) {
            // Deselect: Remove from array and remove class
            selectedDeviceIds = selectedDeviceIds.filter(id => id !== deviceId);
            row.classList.remove('selected-row');
        } else {
            // Select: Add to array and add class
            selectedDeviceIds.push(deviceId);
            row.classList.add('selected-row');
        }

        updateSelectionUI();
    });

    // --- 2. Filter Button Logic ---
    filterButtonsContainer.addEventListener('click', (event) => {
        const button = event.target.closest('.filter-btn');
        if (!button) return;

        const selectedCategory = button.getAttribute('data-category');
        const allRows = devicesTable.querySelectorAll('.device-row');
        const allButtons = filterButtonsContainer.querySelectorAll('.filter-btn');

        // Note: We keep selections even if they are filtered out of view
        // If you want to clear selections when switching filters, uncomment the lines below:
        /*
        selectedDeviceIds = [];
        allRows.forEach(r => r.classList.remove('selected-row'));
        updateSelectionUI();
        */
        
        allButtons.forEach(btn => btn.classList.remove('active-filter'));
        button.classList.add('active-filter');

        allRows.forEach(row => {
            const rowCategory = row.getAttribute('data-category');
            if (selectedCategory === 'All' || rowCategory === selectedCategory) {
                row.style.display = ''; 
            } else {
                row.style.display = 'none'; 
            }
        });
    });

    // Initialize "Show All"
    const allButton = document.querySelector('[data-category="All"]');
    if(allButton) allButton.classList.add('active-filter');

    // Injection of CSS
    const style = document.createElement('style');
    style.textContent = `
        .selected-row {
            background-color: #fce8d5 !important; 
            outline: 2px solid #ff9800;
            z-index: 10;
            position: relative;
        }
        .active-filter {
            background-color: #00bcd4 !important; 
            transform: scale(1.05);
            box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
        }
    `;
    document.head.appendChild(style);
});
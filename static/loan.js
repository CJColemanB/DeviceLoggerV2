document.addEventListener('DOMContentLoaded', () => {
    const filterButtonsContainer = document.getElementById('category_filter_buttons');
    const filterButtons = document.querySelectorAll('.category-filter-btn');
    const deviceTableBody = document.getElementById('device_table_body');
    // Select only the actual data rows (those with data-id), ignoring the "No devices" placeholder row
    const deviceRows = deviceTableBody.querySelectorAll('tr[data-id]'); 
    const selectedDeviceIdInput = document.getElementById('selected_device_id');
    const loanButton = document.getElementById('loan_device_button');
    const deviceSelectMessage = document.getElementById('device_select_message');

    // Initially disable the loan button until a device is selected
    loanButton.disabled = true;

    // Helper function to clear all row selections
    function clearSelection() {
        deviceRows.forEach(r => r.classList.remove('selected-row'));
        selectedDeviceIdInput.value = '';
        deviceSelectMessage.textContent = 'Please click on a device row in the table above to select it.';
        loanButton.disabled = true;
    }

    // --- Filtering Logic (using buttons) ---
    function applyFilter(selectedCategory) {
        // 1. Update button styling: Highlight the active filter button
        filterButtons.forEach(btn => {
            const filterValue = btn.getAttribute('data-filter');
            if (filterValue === selectedCategory) {
                // Active style: blue background, white text
                btn.classList.remove('bg-gray-200', 'text-gray-700', 'hover:bg-blue-100');
                btn.classList.add('bg-blue-600', 'text-white');
            } else {
                // Inactive style: gray background, gray text
                btn.classList.remove('bg-blue-600', 'text-white');
                btn.classList.add('bg-gray-200', 'text-gray-700', 'hover:bg-blue-100');
            }
        });

        // 2. Filter table rows: Hide or show rows based on category
        deviceRows.forEach(row => {
            const category = row.getAttribute('data-category');
            
            // Show all rows if 'All' is selected, otherwise filter by category
            if (selectedCategory === 'All' || category === selectedCategory) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
        
        // 3. Clear any existing device selection when the filter changes
        clearSelection();
    }

    filterButtonsContainer.addEventListener('click', function(event) {
        if (event.target.classList.contains('category-filter-btn')) {
            const selectedCategory = event.target.getAttribute('data-filter');
            applyFilter(selectedCategory);
        }
    });

    // --- Device Selection Toggle Logic ---
    deviceRows.forEach(row => {
        row.addEventListener('click', () => {
            const deviceId = row.getAttribute('data-id');
            const deviceName = row.getAttribute('data-rubric') + '-' + row.getAttribute('data-suffix');
            
            // Check if this row is already selected
            const isSelected = row.classList.contains('selected-row');

            // Clear any previously selected row (important for toggling)
            clearSelection(); 

            if (!isSelected) {
                // If it was NOT selected, select the current row
                row.classList.add('selected-row');

                // Update the hidden input field
                selectedDeviceIdInput.value = deviceId;
                
                // Update the message and enable the button
                deviceSelectMessage.textContent = `Selected Device: ${deviceName} (ID: ${deviceId})`;
                loanButton.disabled = false;
            } 
            // If it WAS selected, clearSelection() already removed the highlight and reset the form fields.
        });
    });

    // Ensure the initial filter is applied and the 'All Devices' button is highlighted on load
    applyFilter('All');
});

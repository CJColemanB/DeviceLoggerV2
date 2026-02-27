document.addEventListener('DOMContentLoaded', () => {
    // --- Logic for Import Modal Confirmation ---
    const importForm = document.getElementById('import-form');
    if (importForm) {
        const fileInput = document.getElementById('import-file-input');
        const modal = document.getElementById('import-modal');
        const cancelBtn = document.getElementById('cancel-import-btn');
        const confirmBtn = document.getElementById('confirm-import-btn');

        // When a file is chosen, show the confirmation modal
        fileInput.addEventListener('change', function() {
            if (this.files.length > 0) {
                modal.classList.remove('hidden');
            }
        });

        // If user cancels, hide modal and reset the file input
        cancelBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
            fileInput.value = ''; // Clear the selected file
        });

        // If user confirms, submit the form
        confirmBtn.addEventListener('click', () => {
            modal.classList.add('hidden');
            importForm.submit();
        });
    }

    // --- Logic for Automatic Rubric ID Generation ---
    const categorySelect = document.getElementById('device_category');
    const rubricInput = document.getElementById('rubric_id_input');
    const suffixInput = document.getElementById('suffix_id_input');

    if (categorySelect && rubricInput && suffixInput) {
        const rubricPrefixes = {
            'Laptop': 'SHC-LQ-',
            'Charger': 'SHC-LP-',
            'iPad': 'SHC-IQ-',
            'Headphones': 'SHC-HP-',
            'Trips': 'SHC-TRIPS-',
            'iPad Charger': 'SHC-IPC-',
            'USBC Charger': 'SHC-UBC-',
            'Other': 'SHC-'
        };

        categorySelect.addEventListener('change', function() {
            const selectedCategory = this.value;
            const prefix = rubricPrefixes[selectedCategory] || '';
            
            // Set the value of the rubric ID input field
            rubricInput.value = prefix;

            // Give focus to the suffix input to encourage completion
            suffixInput.focus();
        });
    }

    // --- Logic for Delete Confirmation ---
    const deleteForms = document.querySelectorAll('.delete-form');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const deviceIdInput = this.querySelector('input[name="delete_id"]');
            if (deviceIdInput) {
                const deviceId = deviceIdInput.value;
                if (!confirm(`Are you sure you want to delete device ID ${deviceId}?`)) {
                    event.preventDefault(); // Stop submission if user cancels
                }
            }
        });
    });
});

// --- Logic for Frontend Sorting (No Page Refresh) ---
// This is outside DOMContentLoaded so the HTML 'onclick' can find it.
const sortDirections = {};

/**
 * Sorts a table based on the column clicked.
 * @param {string} tableId 
 * @param {number} colIndex
 * @param {string} type
 */
function sortTable(tableId, colIndex, type = 'string') {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    // Toggle sort direction
    const sortKey = `${tableId}-${colIndex}`;
    sortDirections[sortKey] = !sortDirections[sortKey]; 
    const isAscending = sortDirections[sortKey];

    // Reset all icons in this table's header to the neutral state
    table.querySelectorAll('.sort-icon').forEach(icon => icon.textContent = '↕');
    
    // Update the specific icon for the column being sorted
    const headerCells = table.querySelectorAll('thead th');
    const currentIcon = headerCells[colIndex].querySelector('.sort-icon');
    if (currentIcon) {
        currentIcon.textContent = isAscending ? '▲' : '▼';
    }

    // Perform the sort
    const sortedRows = rows.sort((a, b) => {
        let valA = a.cells[colIndex].textContent.trim();
        let valB = b.cells[colIndex].textContent.trim();

        if (type === 'number') {
            // Convert to numbers for proper numeric sorting (e.g., 10 > 2)
            const numA = parseFloat(valA.replace(/[^0-9.-]+/g, "")) || 0;
            const numB = parseFloat(valB.replace(/[^0-9.-]+/g, "")) || 0;
            return isAscending ? numA - numB : numB - numA;
        }

        // Standard alphabetical sort
        return isAscending 
            ? valA.localeCompare(valB, undefined, {numeric: true, sensitivity: 'base'}) 
            : valB.localeCompare(valA, undefined, {numeric: true, sensitivity: 'base'});
    });

    // Re-append the rows in the new order
    tbody.append(...sortedRows);
}
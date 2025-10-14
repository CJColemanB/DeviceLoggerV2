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
    // Note: This replaces the inline `onclick` confirm dialogs
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

// This script handles the automatic generation of the device Rubric ID
document.addEventListener('DOMContentLoaded', () => {
    const categorySelect = document.getElementById('device_category');
    const rubricInput = document.getElementById('rubric_id_input');
    const suffixInput = document.getElementById('suffix_id_input');

    // Mapping of category to rubric prefix
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

    // Handle form confirmation for delete action
    // Note: The actual deletion is handled server-side via the POST request
    const deleteForms = document.querySelectorAll('form[name="delete-form"]');
    deleteForms.forEach(form => {
        form.addEventListener('submit', function(event) {
            const deviceId = this.querySelector('input[name="delete_id"]').value;
            if (!confirm(`Are you sure you want to delete device ID ${deviceId}?`)) {
                event.preventDefault();
            }
        });
    });
});

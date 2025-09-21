/**
 * Form Enhancement Script
 * Improves form field styling and functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Apply styling to all form fields
    enhanceFormFields();
    
    // Set up password visibility toggles
    setupPasswordToggles();
});

// Also run immediately in case DOMContentLoaded has already fired
enhanceFormFields();
setupPasswordToggles();

/**
 * Enhances all form fields with proper styling
 */
function enhanceFormFields() {
    // Text inputs, email, password, etc.
    const formInputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="tel"], input[type="number"], input[type="date"], textarea, select');
    
    formInputs.forEach(input => {
        // Add styling classes
        input.classList.add('form-input');
        
        // Ensure text color is visible
        input.style.color = '#1f2937'; // Dark gray
        
        // Add border and other styles
        input.style.border = '2px solid #e5e7eb';
        input.style.borderRadius = '0.5rem';
        input.style.padding = '0.75rem 1rem';
        input.style.width = '100%';
        input.style.backgroundColor = '#ffffff';
        input.style.fontSize = '1rem';
        input.style.lineHeight = '1.5';
        input.style.transition = 'all 0.2s ease-in-out';
        
        // Focus event
        input.addEventListener('focus', function() {
            this.style.outline = 'none';
            this.style.borderColor = '#3b82f6'; // Blue
            this.style.boxShadow = '0 0 0 3px rgba(59, 130, 246, 0.2)'; // Soft blue glow
        });
        
        // Blur event
        input.addEventListener('blur', function() {
            this.style.boxShadow = 'none';
            if (!this.value) {
                this.style.borderColor = '#e5e7eb'; // Reset to gray
            }
        });
    });
    
    // Style checkboxes
    const checkboxes = document.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach(checkbox => {
        checkbox.style.width = '1.25rem';
        checkbox.style.height = '1.25rem';
        checkbox.style.borderRadius = '0.25rem';
        checkbox.style.border = '2px solid #e5e7eb';
        checkbox.style.backgroundColor = '#ffffff';
        checkbox.style.cursor = 'pointer';
    });
}

/**
 * Sets up password visibility toggles
 */
function setupPasswordToggles() {
    // Password toggle buttons
    const toggleButtons = document.querySelectorAll('.toggle-password, .toggle-password-confirm');
    
    toggleButtons.forEach(toggle => {
        // Style the toggle button
        toggle.style.cursor = 'pointer';
        toggle.style.color = '#6b7280';
        
        // Add hover effect
        toggle.addEventListener('mouseenter', function() {
            this.style.color = '#3b82f6';
        });
        
        toggle.addEventListener('mouseleave', function() {
            this.style.color = '#6b7280';
        });
        
        // Set up click event if not already set
        if (!toggle.hasClickListener) {
            toggle.addEventListener('click', function() {
                // Find the password input
                const passwordInput = this.previousElementSibling || 
                                     this.parentElement.querySelector('input[type="password"]');
                
                if (passwordInput) {
                    // Toggle password visibility
                    const type = passwordInput.getAttribute('type') === 'password' ? 'text' : 'password';
                    passwordInput.setAttribute('type', type);
                    
                    // Toggle eye icon
                    const eyeIcon = this.querySelector('i');
                    if (eyeIcon) {
                        eyeIcon.classList.toggle('fa-eye');
                        eyeIcon.classList.toggle('fa-eye-slash');
                    }
                }
            });
            
            // Mark as having a click listener to prevent duplicates
            toggle.hasClickListener = true;
        }
    });
}

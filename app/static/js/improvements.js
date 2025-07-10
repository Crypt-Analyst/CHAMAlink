// ChamaLink Enhanced UI/UX JavaScript

// Utility Functions
const ChamaLink = {
    // Show loading state on buttons
    showButtonLoading: function(button, text = 'Loading...') {
        if (typeof button === 'string') {
            button = document.querySelector(button);
        }
        
        if (button) {
            button.disabled = true;
            button.classList.add('btn-loading');
            button.setAttribute('data-original-text', button.innerHTML);
            button.innerHTML = `<span class="loading-spinner me-2"></span>${text}`;
        }
    },
    
    // Hide loading state on buttons
    hideButtonLoading: function(button) {
        if (typeof button === 'string') {
            button = document.querySelector(button);
        }
        
        if (button) {
            button.disabled = false;
            button.classList.remove('btn-loading');
            const originalText = button.getAttribute('data-original-text');
            if (originalText) {
                button.innerHTML = originalText;
                button.removeAttribute('data-original-text');
            }
        }
    },
    
    // Show toast notification
    showToast: function(message, type = 'info', duration = 5000) {
        // Create toast container if it doesn't exist
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        
        // Create toast
        const toast = document.createElement('div');
        toast.className = `toast toast-${type} show`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="toast-header">
                <i class="fas fa-${this.getToastIcon(type)} me-2"></i>
                <strong class="me-auto">${this.getToastTitle(type)}</strong>
                <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        container.appendChild(toast);
        
        // Auto-remove after duration
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, duration);
        
        // Manual close
        toast.querySelector('.btn-close').onclick = () => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        };
    },
    
    getToastIcon: function(type) {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-triangle',
            warning: 'exclamation-triangle',
            info: 'info-circle'
        };
        return icons[type] || 'info-circle';
    },
    
    getToastTitle: function(type) {
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Information'
        };
        return titles[type] || 'Notification';
    },
    
    // Validate password strength
    checkPasswordStrength: function(password) {
        let score = 0;
        let feedback = [];
        
        if (password.length >= 8) score++;
        else feedback.push('At least 8 characters');
        
        if (/[a-z]/.test(password)) score++;
        else feedback.push('Lowercase letter');
        
        if (/[A-Z]/.test(password)) score++;
        else feedback.push('Uppercase letter');
        
        if (/\d/.test(password)) score++;
        else feedback.push('Number');
        
        if (/[^a-zA-Z\d]/.test(password)) score++;
        else feedback.push('Special character');
        
        const levels = ['weak', 'weak', 'fair', 'good', 'strong'];
        return {
            score: score,
            level: levels[score] || 'weak',
            feedback: feedback
        };
    },
    
    // Setup password strength indicator
    setupPasswordStrength: function(passwordInput, strengthContainer) {
        if (typeof passwordInput === 'string') {
            passwordInput = document.querySelector(passwordInput);
        }
        if (typeof strengthContainer === 'string') {
            strengthContainer = document.querySelector(strengthContainer);
        }
        
        if (!passwordInput || !strengthContainer) return;
        
        strengthContainer.innerHTML = `
            <div class="password-strength-bar">
                <div class="password-strength-fill"></div>
            </div>
            <small class="text-muted mt-1 d-block password-feedback"></small>
        `;
        
        passwordInput.addEventListener('input', function() {
            const strength = ChamaLink.checkPasswordStrength(this.value);
            const container = strengthContainer.querySelector('.password-strength-bar').parentElement;
            const fill = strengthContainer.querySelector('.password-strength-fill');
            const feedback = strengthContainer.querySelector('.password-feedback');
            
            // Update classes
            container.className = `password-strength ${strength.level}`;
            
            // Update feedback
            if (this.value.length > 0) {
                if (strength.level === 'strong') {
                    feedback.textContent = 'Strong password!';
                    feedback.className = 'text-success mt-1 d-block password-feedback';
                } else {
                    feedback.textContent = `Needs: ${strength.feedback.join(', ')}`;
                    feedback.className = 'text-muted mt-1 d-block password-feedback';
                }
            } else {
                feedback.textContent = '';
            }
        });
    },
    
    // Enhanced form validation
    validateForm: function(form) {
        if (typeof form === 'string') {
            form = document.querySelector(form);
        }
        
        if (!form) return false;
        
        let isValid = true;
        const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
        
        inputs.forEach(input => {
            const value = input.value.trim();
            
            // Remove previous validation classes
            input.classList.remove('is-valid', 'is-invalid');
            
            if (!value) {
                input.classList.add('is-invalid');
                isValid = false;
            } else {
                // Email validation
                if (input.type === 'email') {
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        input.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        input.classList.add('is-valid');
                    }
                }
                // Phone validation (Kenyan format)
                else if (input.type === 'tel' || input.name === 'phone_number') {
                    const phoneRegex = /^(\+254|0)[17]\d{8}$/;
                    if (!phoneRegex.test(value)) {
                        input.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        input.classList.add('is-valid');
                    }
                }
                // Password validation
                else if (input.type === 'password') {
                    const strength = this.checkPasswordStrength(value);
                    if (strength.score < 2) {
                        input.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        input.classList.add('is-valid');
                    }
                }
                else {
                    input.classList.add('is-valid');
                }
            }
        });
        
        return isValid;
    },
    
    // Setup form auto-validation
    setupFormValidation: function(form) {
        if (typeof form === 'string') {
            form = document.querySelector(form);
        }
        
        if (!form) return;
        
        const inputs = form.querySelectorAll('input, select, textarea');
        
        inputs.forEach(input => {
            input.addEventListener('blur', () => {
                this.validateForm(form);
            });
        });
    },
    
    // Loading overlay
    showLoadingOverlay: function(container, message = 'Loading...') {
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        
        if (!container) return;
        
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay position-absolute top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center bg-white bg-opacity-75';
        overlay.style.zIndex = '1000';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner mb-2"></div>
                <div class="text-muted">${message}</div>
            </div>
        `;
        
        container.style.position = 'relative';
        container.appendChild(overlay);
    },
    
    hideLoadingOverlay: function(container) {
        if (typeof container === 'string') {
            container = document.querySelector(container);
        }
        
        if (container) {
            const overlay = container.querySelector('.loading-overlay');
            if (overlay) {
                overlay.remove();
            }
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Setup password strength indicators
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        const container = input.closest('.form-group, .mb-3')?.querySelector('.password-strength') ||
                         input.parentElement.querySelector('.password-strength');
        if (container) {
            ChamaLink.setupPasswordStrength(input, container);
        }
    });
    
    // Setup form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        ChamaLink.setupFormValidation(form);
    });
    
    // Enhanced button click handling
    document.addEventListener('click', function(e) {
        const button = e.target.closest('button[type="submit"], .btn-async');
        if (button && button.form) {
            if (ChamaLink.validateForm(button.form)) {
                ChamaLink.showButtonLoading(button);
                
                // Auto-hide loading after 10 seconds (fallback)
                setTimeout(() => {
                    ChamaLink.hideButtonLoading(button);
                }, 10000);
            } else {
                e.preventDefault();
            }
        }
    });
    
    // Auto-show flash messages as toasts
    const flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(alert => {
        const type = alert.classList.contains('alert-success') ? 'success' :
                    alert.classList.contains('alert-danger') ? 'error' :
                    alert.classList.contains('alert-warning') ? 'warning' : 'info';
        
        ChamaLink.showToast(alert.textContent.trim(), type);
        alert.style.display = 'none'; // Hide original alert
    });
});

// Export for global use
window.ChamaLink = ChamaLink;

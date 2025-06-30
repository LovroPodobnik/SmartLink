// Main JavaScript functionality for SmartLink

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize copy buttons
    initializeCopyButtons();
    
    // Initialize form validation
    initializeFormValidation();
    
    // Initialize analytics refresh
    initializeAnalyticsRefresh();
}

// Initialize Bootstrap tooltips
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize copy to clipboard functionality
function initializeCopyButtons() {
    document.querySelectorAll('[data-copy]').forEach(button => {
        button.addEventListener('click', function() {
            const text = this.getAttribute('data-copy');
            copyToClipboard(text);
        });
    });
}

// Copy text to clipboard with visual feedback
function copyToClipboard(text) {
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(function() {
            showToast('Link copied to clipboard!', 'success');
        }).catch(function() {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// Fallback copy method for older browsers
function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.top = '-1000px';
    textArea.style.left = '-1000px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        const successful = document.execCommand('copy');
        if (successful) {
            showToast('Link copied to clipboard!', 'success');
        } else {
            showToast('Copy failed. Please copy manually.', 'error');
        }
    } catch (err) {
        showToast('Copy not supported. Please copy manually.', 'error');
    }
    
    document.body.removeChild(textArea);
}

// Show toast notification
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;
    toast.textContent = message;
    
    // Style based on type
    const colors = {
        success: '#00b894',
        error: '#e17055',
        warning: '#fdcb6e',
        info: '#74b9ff'
    };
    
    toast.style.backgroundColor = colors[type] || colors.info;
    
    document.body.appendChild(toast);
    
    // Animate in
    setTimeout(() => {
        toast.style.opacity = '1';
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Remove after delay
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        setTimeout(() => {
            if (toast.parentNode) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, 3000);
}

// Form validation enhancement
function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focus on first invalid field
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
        
        // Real-time validation
        const inputs = form.querySelectorAll('input, textarea, select');
        inputs.forEach(input => {
            input.addEventListener('blur', function() {
                validateField(this);
            });
            
            input.addEventListener('input', function() {
                if (this.classList.contains('is-invalid')) {
                    validateField(this);
                }
            });
        });
    });
}

// Validate individual field
function validateField(field) {
    const isValid = field.checkValidity();
    
    field.classList.remove('is-valid', 'is-invalid');
    field.classList.add(isValid ? 'is-valid' : 'is-invalid');
    
    // Custom validation messages
    const feedback = field.parentNode.querySelector('.invalid-feedback');
    if (feedback && !isValid) {
        if (field.validity.valueMissing) {
            feedback.textContent = 'This field is required.';
        } else if (field.validity.typeMismatch) {
            if (field.type === 'email') {
                feedback.textContent = 'Please enter a valid email address.';
            } else if (field.type === 'url') {
                feedback.textContent = 'Please enter a valid URL.';
            }
        } else if (field.validity.tooShort) {
            feedback.textContent = `Minimum length is ${field.minLength} characters.`;
        } else if (field.validity.tooLong) {
            feedback.textContent = `Maximum length is ${field.maxLength} characters.`;
        }
    }
}

// Analytics refresh functionality
function initializeAnalyticsRefresh() {
    const refreshButton = document.querySelector('[data-refresh-analytics]');
    if (refreshButton) {
        refreshButton.addEventListener('click', function() {
            refreshAnalytics();
        });
    }
    
    // Auto-refresh every 5 minutes on analytics page
    if (document.querySelector('#dailyClicksChart')) {
        setInterval(refreshAnalytics, 5 * 60 * 1000);
    }
}

// Refresh analytics data
function refreshAnalytics() {
    const refreshButton = document.querySelector('[data-refresh-analytics]');
    if (refreshButton) {
        const originalText = refreshButton.innerHTML;
        refreshButton.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Refreshing...';
        refreshButton.disabled = true;
        
        setTimeout(() => {
            refreshButton.innerHTML = originalText;
            refreshButton.disabled = false;
            showToast('Analytics refreshed!', 'success');
        }, 1000);
    }
}

// URL validation helper
function isValidUrl(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Format numbers with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

// Format percentage
function formatPercentage(value, total) {
    if (total === 0) return '0%';
    return ((value / total) * 100).toFixed(1) + '%';
}

// Debounce function for input events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Show loading state
function showLoading(element) {
    element.classList.add('loading');
    element.style.pointerEvents = 'none';
}

// Hide loading state
function hideLoading(element) {
    element.classList.remove('loading');
    element.style.pointerEvents = 'auto';
}

// Smooth scroll to element
function scrollToElement(element, offset = 0) {
    const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
    const offsetPosition = elementPosition - offset;
    
    window.scrollTo({
        top: offsetPosition,
        behavior: 'smooth'
    });
}

// Check if element is in viewport
function isInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

// Animate elements when they come into view
function animateOnScroll() {
    const elements = document.querySelectorAll('.animate-on-scroll');
    
    elements.forEach(element => {
        if (isInViewport(element)) {
            element.classList.add('animated');
        }
    });
}

// Initialize scroll animations
window.addEventListener('scroll', debounce(animateOnScroll, 10));

// Export functions for use in other scripts
window.SmartLink = {
    copyToClipboard,
    showToast,
    validateField,
    formatNumber,
    formatPercentage,
    isValidUrl,
    showLoading,
    hideLoading
};

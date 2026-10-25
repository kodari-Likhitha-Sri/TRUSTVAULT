// TrustVault Client Interactivity & Modern UI Helpers

document.addEventListener('DOMContentLoaded', function () {
    // 1. Initialize Bootstrap Tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // 2. Auto-dismiss alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            try {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            } catch (e) {}
        }, 5000);
    });

    // 3. Demo Login Autofill
    const demoButtons = document.querySelectorAll('.demo-login-btn');
    demoButtons.forEach(btn => {
        btn.addEventListener('click', function () {
            const emailInput = document.getElementById('login_id');
            const passInput = document.getElementById('password');
            if (emailInput && passInput) {
                emailInput.value = this.dataset.email;
                passInput.value = this.dataset.password;
                emailInput.focus();
            }
        });
    });

    // 4. Password Toggle
    const togglePasswordBtn = document.getElementById('toggle-password');
    if (togglePasswordBtn) {
        togglePasswordBtn.addEventListener('click', function () {
            const passInput = document.getElementById('password');
            const eyeIcon = this.querySelector('i');
            if (passInput) {
                if (passInput.type === 'password') {
                    passInput.type = 'text';
                    if (eyeIcon) {
                        eyeIcon.classList.remove('bi-eye');
                        eyeIcon.classList.add('bi-eye-slash');
                    }
                } else {
                    passInput.type = 'password';
                    if (eyeIcon) {
                        eyeIcon.classList.remove('bi-eye-slash');
                        eyeIcon.classList.add('bi-eye');
                    }
                }
            }
        });
    }
});

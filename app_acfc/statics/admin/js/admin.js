// Fonction pour la validation des mots de passe
document.addEventListener("DOMContentLoaded", () => {
    const newPasswordInput = document.getElementById("new_password");
    const conditions = {
        cond1: (password) => password.length >= 15,
        cond2: (password) => /[A-Z]/.test(password),
        cond3: (password) => /[a-z]/.test(password),
        cond4: (password) => /\d/.test(password),
        cond5: (password) => /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };

    if (newPasswordInput) {
        newPasswordInput.addEventListener("input", () => {
            const password = newPasswordInput.value;

            for (const [cond, check] of Object.entries(conditions)) {
                const span = document.querySelector(`.${cond}`);
                if (span) {
                    span.textContent = check(password) ? "✅" : "❌";
                }
            }
        });
    }
});

// Fonction de vérification de concordance du nouveau mot de passe
document.addEventListener("DOMContentLoaded", () => {
    const newPasswordInput = document.getElementById("new_password");
    const confirmPasswordInput = document.getElementById("confirm_password");
    const matchIndicator = document.getElementById("password_match");

    confirmPasswordInput.addEventListener("input", () => {
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        if (matchIndicator) {
            matchIndicator.textContent = "";
            const message = document.createElement("p");
            message.textContent = newPassword === confirmPassword ? "✅ Les mots de passe correspondent" : "❌ Les mots de passe ne correspondent pas";
            matchIndicator.innerHTML = "";
            matchIndicator.appendChild(message);
        }
    });
});
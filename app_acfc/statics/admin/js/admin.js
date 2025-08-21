// Centralise la logique de validation et d'UI pour le changement de mot de passe
document.addEventListener("DOMContentLoaded", () => {
    const newPasswordInput = document.getElementById("new_password");
    const oldPasswordInput = document.getElementById("old_password");
    const confirmPasswordInput = document.getElementById("confirm_password");
    const matchIndicator = document.getElementById("password_match");
    const form = document.querySelector("form");
    const submitButton = form ? form.querySelector("button[type='submit']") : null;

    const conditions = {
        cond1: (password) => password.length >= 15,
        cond2: (password) => /[A-Z]/.test(password),
        cond3: (password) => /[a-z]/.test(password),
        cond4: (password) => /\d/.test(password),
        cond5: (password) => /[!@#$%^&*(),.?":{}|<>]/.test(password),
    };

    const updateConditions = (password) => {
        for (const [cond, check] of Object.entries(conditions)) {
            const span = document.querySelector(`.${cond}`);
            if (span) span.textContent = check(password) ? "✅" : "❌";
        }
    };

    const updateMatchIndicator = () => {
        if (!matchIndicator || !newPasswordInput || !confirmPasswordInput) return;
        matchIndicator.innerHTML = "";
        const message = document.createElement("p");
        if (newPasswordInput.value === "" && confirmPasswordInput.value === "") {
            // rien à afficher si vide
            return;
        }
        message.textContent = newPasswordInput.value === confirmPasswordInput.value ? "✅ Les mots de passe correspondent" : "❌ Les mots de passe ne correspondent pas";
        matchIndicator.appendChild(message);
    };

    const toggleSubmitButton = () => {
        if (!submitButton) return;
        const isFormValid = (oldPasswordInput && oldPasswordInput.value) && (newPasswordInput && newPasswordInput.value) && (confirmPasswordInput && confirmPasswordInput.value);
        const allConditionsMet = newPasswordInput ? Object.values(conditions).every((check) => check(newPasswordInput.value)) : false;
        const passwordsMatch = newPasswordInput && confirmPasswordInput ? newPasswordInput.value === confirmPasswordInput.value : false;
        submitButton.disabled = !(isFormValid && allConditionsMet && passwordsMatch);
    };

    // listeners
    if (newPasswordInput) {
        newPasswordInput.addEventListener("input", () => {
            updateConditions(newPasswordInput.value);
            updateMatchIndicator();
            toggleSubmitButton();
        });
        // initial update
        updateConditions(newPasswordInput.value);
    }

    if (confirmPasswordInput) {
        confirmPasswordInput.addEventListener("input", () => {
            updateMatchIndicator();
            toggleSubmitButton();
        });
    }

    if (oldPasswordInput) {
        oldPasswordInput.addEventListener("input", toggleSubmitButton);
    }

    // état initial du bouton
    if (submitButton) submitButton.disabled = true;
});
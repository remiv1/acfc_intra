const editBtn = document.getElementById('edit-parameters');
const fieldset = document.getElementById('accountFieldset');
const saveBtn = document.getElementById('save-parameters');

editBtn.addEventListener('click', () => {
const isDisabled = fieldset.hasAttribute('disabled');

if (isDisabled) {
    fieldset.removeAttribute('disabled');
    saveBtn.removeAttribute('disabled');
    editBtn.textContent = 'Annuler';
    editBtn.classList.replace('btn-outline-primary', 'btn-outline-danger');
} else {
    fieldset.setAttribute('disabled', '');
    saveBtn.setAttribute('disabled', '');
    editBtn.textContent = 'Modifier';
    editBtn.classList.replace('btn-outline-danger', 'btn-outline-primary');
}
});

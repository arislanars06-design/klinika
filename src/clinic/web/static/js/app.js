/* Clinic LOR — web app scripts (Phase 1) */

// Bootstrap-style form validation.
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".needs-validation").forEach((form) => {
    form.addEventListener("submit", (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });

  // When user picks a suggested patient from autocomplete, copy the data-id
  // (patient_id) into the hidden field so save picks the existing record.
  const fullNameInput = document.querySelector('input[name="full_name"]');
  const patientIdField = document.querySelector('input[name="patient_id"]');
  const suggestions = document.getElementById("patient-suggestions");
  if (fullNameInput && patientIdField && suggestions) {
    fullNameInput.addEventListener("input", () => {
      const match = Array.from(suggestions.options).find(
        (opt) => opt.value === fullNameInput.value,
      );
      patientIdField.value = match ? match.dataset.id || "" : "";
    });
  }
});

/**
 * Smart Campus Hostel ERP - Standard Vanilla JS Portal Enhancements
 */
document.addEventListener("DOMContentLoaded", function () {
    // 1. Day Leave vs Night Leave Dynamic Form Handling
    const leaveTypeRadios = document.querySelectorAll('input[name="leave_type"]');
    const returnDateField = document.getElementById("expected_return_date");
    const returnTimeField = document.getElementById("expected_return_time");
    const destinationField = document.getElementById("destination");
    const startDateField = document.getElementById("start_date");
    const dayCurfewNotice = document.getElementById("day-curfew-notice");
    const destinationRequiredNotice = document.getElementById("destination-required-badge");

    function updateLeaveFormMode(selectedType) {
        if (!returnDateField || !returnTimeField) return;

        if (selectedType === "Day Leave") {
            // Lock return date to departure date
            if (startDateField && startDateField.value) {
                returnDateField.value = startDateField.value;
            }
            returnDateField.setAttribute("readonly", "readonly");
            
            // Set max time for return
            returnTimeField.setAttribute("max", "21:00");
            if (dayCurfewNotice) dayCurfewNotice.classList.remove("d-none");
            if (destinationRequiredNotice) destinationRequiredNotice.classList.add("d-none");
            if (destinationField) {
                destinationField.removeAttribute("required");
                destinationField.setAttribute("placeholder", "Optional for Day Outing (Defaults to Campus Vicinity)");
            }
        } else {
            // Night Leave
            returnDateField.removeAttribute("readonly");
            returnTimeField.removeAttribute("max");
            if (dayCurfewNotice) dayCurfewNotice.classList.add("d-none");
            if (destinationRequiredNotice) destinationRequiredNotice.classList.remove("d-none");
            if (destinationField) {
                destinationField.setAttribute("required", "required");
                destinationField.setAttribute("placeholder", "Complete destination address (e.g. Home, Outstation Hotel)");
            }
        }
    }

    if (leaveTypeRadios.length > 0) {
        leaveTypeRadios.forEach(radio => {
            radio.addEventListener("change", function () {
                updateLeaveFormMode(this.value);
            });
            if (radio.checked) {
                updateLeaveFormMode(radio.value);
            }
        });
    }

    if (startDateField && returnDateField) {
        startDateField.addEventListener("change", function () {
            const activeRadio = document.querySelector('input[name="leave_type"]:checked');
            if (activeRadio && activeRadio.value === "Day Leave") {
                returnDateField.value = this.value;
            }
            returnDateField.setAttribute("min", this.value);
        });
    }

    // 2. Generic Table Search Filters
    function setupTableFilter(inputId, tableId) {
        const input = document.getElementById(inputId);
        const table = document.getElementById(tableId);
        if (!input || !table) return;

        input.addEventListener("keyup", function () {
            const filter = input.value.toLowerCase();
            const rows = table.querySelectorAll("tbody tr");

            rows.forEach(row => {
                const text = row.innerText.toLowerCase();
                if (text.includes(filter)) {
                    row.style.display = "";
                } else {
                    row.style.display = "none";
                }
            });
        });
    }

    setupTableFilter("search-leaves-input", "leaves-table");
    setupTableFilter("search-tickets-input", "tickets-table");
    setupTableFilter("warden-leaves-search", "warden-leaves-table");
    setupTableFilter("warden-tickets-search", "warden-tickets-table");
});

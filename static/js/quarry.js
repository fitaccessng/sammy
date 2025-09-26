// Profile Actions Handler
const initProfileActions = () => {
    document.querySelectorAll('.p-6 button').forEach(button => {
        button.addEventListener('click', function() {
            const action = this.querySelector('span.text-sm').textContent;
            switch(action) {
                case 'Change Password':
                    window.location.href = '/quarry/settings#password';
                    break;
                case 'Notification Preferences':
                    window.location.href = '/quarry/settings#notifications';
                    break;
                case 'Activity Log':
                    window.location.href = '/quarry/activity-log';
                    break;
            }
        });
    });
};

// Safety Page Handlers
const initSafetyPage = () => {
    const incidentBtn = document.querySelector('#logIncidentBtn');
    if (incidentBtn) {
        incidentBtn.addEventListener('click', () => {
            // Add incident logging logic
            console.log('Logging incident...');
        });
    }

    const inspectionBtn = document.querySelector('#scheduleInspectionBtn');
    if (inspectionBtn) {
        inspectionBtn.addEventListener('click', () => {
            // Add inspection scheduling logic
            console.log('Scheduling inspection...');
        });
    }

    // Filter records
    const filterSelect = document.querySelector('#recordFilter');
    if (filterSelect) {
        filterSelect.addEventListener('change', (e) => {
            const value = e.target.value;
            // Add filtering logic
            console.log(`Filtering by: ${value}`);
        });
    }
};

// Initialize all components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initProfileActions();
    initSafetyPage();
});
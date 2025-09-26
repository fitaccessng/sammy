document.addEventListener('DOMContentLoaded', function() {
    // Document Upload
    const uploadForm = document.getElementById('uploadForm');
    if (uploadForm) {
        uploadForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(uploadForm);
            try {
                const response = await fetch('/finance/documents/upload', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.status === 'success') {
                    showAlert('Document uploaded successfully', 'success');
                }
            } catch (error) {
                showAlert('Error uploading document', 'error');
            }
        });
    }

    // Report Generation
    const reportForm = document.getElementById('reportForm');
    if (reportForm) {
        reportForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(reportForm);
            try {
                const response = await fetch('/finance/reports/generate', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.status === 'success') {
                    window.location.href = `/finance/reports/download/${data.report_id}`;
                }
            } catch (error) {
                showAlert('Error generating report', 'error');
            }
        });
    }

    // Bank Reconciliation
    const reconcileForm = document.getElementById('reconcileForm');
    if (reconcileForm) {
        reconcileForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(reconcileForm);
            try {
                const response = await fetch('/finance/bank-reconciliation/reconcile', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                if (data.status === 'success') {
                    showAlert('Reconciliation completed successfully', 'success');
                }
            } catch (error) {
                showAlert('Error during reconciliation', 'error');
            }
        });
    }

    // Utility Functions
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `fixed top-4 right-4 p-4 rounded-lg ${
            type === 'success' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
        }`;
        alertDiv.textContent = message;
        document.body.appendChild(alertDiv);
        setTimeout(() => alertDiv.remove(), 3000);
    }
});
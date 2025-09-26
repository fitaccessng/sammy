// Chart initialization
const initCharts = () => {
    const monthlySpendData = JSON.parse(document.getElementById('monthlySpendData').textContent);
    const topCategoriesData = JSON.parse(document.getElementById('topCategoriesData').textContent);

    if (document.getElementById('spendTrendsChart')) {
        const spendCtx = document.getElementById('spendTrendsChart').getContext('2d');
        new Chart(spendCtx, {
            type: 'line',
            data: {
                labels: monthlySpendData.map(item => item.month),
                datasets: [{
                    label: 'Monthly Spend',
                    data: monthlySpendData.map(item => item.amount),
                    borderColor: 'rgb(59, 130, 246)',
                    tension: 0.1,
                    fill: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                layout: {
                    padding: {
                        top: 5,
                        right: 15,
                        bottom: 5,
                        left: 15
                    }
                },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'center'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            callback: function(value) {
                                return '₦' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }

    if (document.getElementById('categoryChart')) {
        const categoryCtx = document.getElementById('categoryChart').getContext('2d');
        new Chart(categoryCtx, {
            type: 'doughnut',
            data: {
                labels: topCategoriesData.map(item => item.category),
                datasets: [{
                    data: topCategoriesData.map(item => item.spend),
                    backgroundColor: [
                        'rgb(59, 130, 246)',
                        'rgb(16, 185, 129)',
                        'rgb(249, 115, 22)',
                        'rgb(139, 92, 246)'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                layout: {
                    padding: 20
                },
                plugins: {
                    legend: {
                        position: 'right',
                        align: 'center'
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const value = context.raw;
                                return ' ₦' + value.toLocaleString();
                            }
                        }
                    }
                }
            }
        });
    }
};

// Settings form handling
const initSettingsForm = () => {
    const settingsForm = document.getElementById('settingsForm');
    if (settingsForm) {
        settingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(settingsForm);
            try {
                const response = await fetch('/procurement/settings/update', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': document.querySelector('meta[name="csrf-token"]').content
                    },
                    body: JSON.stringify(Object.fromEntries(formData))
                });
                const data = await response.json();
                if (data.status === 'success') {
                    alert('Settings updated successfully');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error updating settings');
            }
        });
    }
};

// Initialize all components
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    initSettingsForm();
});
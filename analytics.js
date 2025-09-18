// Booking Trends Chart
new Chart(document.getElementById('bookingTrendsChart').getContext('2d'), {
    type: 'line',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
            label: 'Bookings',
            data: [120, 150, 180, 220, 190, 240],
            borderColor: '#667eea',
            backgroundColor: 'rgba(102,126,234,0.1)',
            tension: 0.4,
            fill: true
        }]
    },
    options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
    }
});
// Classroom Utilization Chart
new Chart(document.getElementById('utilizationChart').getContext('2d'), {
    type: 'bar',
    data: {
        labels: ['Room A', 'Room B', 'Lab 101', 'Lab 102', 'Hall A'],
        datasets: [{
            label: 'Utilization %',
            data: [94, 87, 92, 78, 85],
            backgroundColor: '#a5b4fc'
        }]
    },
    options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, max: 100 } }
    }
});
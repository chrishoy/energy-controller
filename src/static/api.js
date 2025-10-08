// Function to update the rates display
function updateRates() {
    console.log('Fetching updated rates...');
    Promise.all([
        fetch('/api/rates').then(response => response.json()),
        fetch('/api/heating-schedule').then(response => response.json())
    ])
        .then(([rateData, heatingData]) => {
            console.log('Received new rate data:', rateData);
            console.log('Received heating schedule:', heatingData);

            // Update current rate
            if (rateData.current) {
                document.getElementById('current-price').textContent =
                    rateData.current.value_inc_vat.toFixed(2);
                document.getElementById('as-at').textContent =
                    formatDate(rateData.as_at);
                document.getElementById('valid-until').textContent =
                    formatDate(rateData.current.valid_to);
                document.getElementById('rates-updated').textContent =
                    formatDate(rateData.data_read_at);
            }

            // Update heating schedule summary
            if (heatingData.summary) {
                const summary = heatingData.summary;
                document.getElementById('heating-summary').innerHTML = `
                    <p><strong>Total Cost:</strong> £${summary.total_cost.toFixed(3)}</p>
                    <p><strong>Heating Hours:</strong> ${summary.on_hours.toFixed(1)} hours</p>
                    <p><strong>Average Price When On:</strong> ${summary.average_on_price ? summary.average_on_price.toFixed(2) : 'N/A'} p/kWh</p>
                    <p><strong>Comfort Coverage:</strong> ${summary.warm_comfort_slots}/${summary.comfort_slots} slots</p>
                    <p><strong>Total Transitions:</strong> ${heatingData.transitions ? heatingData.transitions.length : 0}</p>
                `;
            }

            // Update chart
            updateChart(rateData, heatingData);
        })
        .catch(error => {
            console.error('Error fetching rates:', error);
        });
    console.log('Update cycle completed');
}

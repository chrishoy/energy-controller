// Function to update the chart with new data
function updateChart(rateData, heatingData) {
    console.log('Creating chart with', rateData.latest.length, 'data points');
    const timeLabels = rateData.latest.map(rate => {
        const date = new Date(rate.valid_from);
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
    const values = rateData.latest.map(rate => rate.value_inc_vat);
    console.log('Chart data prepared:', { timeLabels: timeLabels.length, values: values.length });

    // Destroy existing chart if it exists
    if (window.rateChart) {
        window.rateChart.destroy();
    }

    const canvas = document.getElementById('ratesChart');
    if (!canvas) {
        console.error('Canvas element not found!');
        return;
    }
    const ctx = canvas.getContext('2d');
    console.log('Chart context created, creating chart...');
    console.log('Canvas dimensions:', canvas.width, 'x', canvas.height);

    // Create heating periods data for background fill
    const heatingPeriods = generateHeatingPeriods(heatingData, rateData);

    window.rateChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: timeLabels,
            datasets: [
                // Heating background areas
                ...heatingPeriods,
                // Main price line
                {
                    label: 'Rate (p/kWh)',
                    data: values,
                    borderColor: 'rgb(75, 192, 192)',
                    backgroundColor: 'rgba(75, 192, 192, 0.1)',
                    stepped: 'before',  // This creates the step effect
                    pointRadius: 1,     // Small points at the corners
                    pointHoverRadius: 5,
                    fill: true, // Fill the area under the line
                    tension: 0
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    beginAtZero: false // Set to false since we're using fill: '+1'
                },
                x: {
                    title: {
                        display: false
                    },
                    ticks: {
                        callback: function (value, index) {
                            return timeLabels[index];
                        }
                    },
                    grid: {
                        display: false  // Remove vertical grid lines
                    },
                    // Add extra padding at bottom for date labels
                    afterFit: function (scale) {
                        scale.paddingBottom = 35;  // Adjusted padding for date labels
                    }
                },
                x2: {
                    type: 'category',
                    position: 'bottom',
                    grid: {
                        display: false  // Remove vertical grid lines
                    },
                    border: {
                        display: false
                    },
                    ticks: {
                        maxRotation: 0,
                        minRotation: 0,
                        padding: 15,  // Adjusted padding for better spacing
                        autoSkip: false,  // Don't skip any ticks
                        callback: function (value, index) {
                            if (!rateData.latest || index >= rateData.latest.length) return '';

                            const date = new Date(rateData.latest[index].valid_from);
                            const currentDay = date.getDate();

                            // Find the start and end indices for the current date
                            let firstIndex = index;
                            let lastIndex = index;

                            // Look backwards to find first entry for this date
                            while (firstIndex > 0 &&
                                new Date(rateData.latest[firstIndex - 1].valid_from).getDate() === currentDay) {
                                firstIndex--;
                            }

                            // Look forwards to find last entry for this date
                            while (lastIndex < rateData.latest.length - 1 &&
                                new Date(rateData.latest[lastIndex + 1].valid_from).getDate() === currentDay) {
                                lastIndex++;
                            }

                            // Show markers at actual first and last data points for the date
                            if (index === firstIndex || index === lastIndex) {
                                return '|';
                            }

                            // Show date label at center point between first and last actual data points
                            const centerIndex = Math.floor((firstIndex + lastIndex) / 2);
                            if (index === centerIndex) {
                                return date.toLocaleDateString([],
                                    { weekday: 'short', month: 'short', day: 'numeric' });
                            }

                            return '';
                        }
                    }
                }
            },
            animation: {
                duration: 0 // Disable animation for smoother updates
            },
            plugins: {
                legend: {
                    display: true,
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        padding: 20,
                        filter: function (legendItem, chartData) {
                            // Hide datasets with empty labels (heating periods)
                            return legendItem.text !== '';
                        }
                    }
                },
                annotation: {
                    annotations: {
                        currentTime: {
                            type: 'line',
                            scaleID: 'x',
                            value: function (ctx) {
                                const asAtDate = new Date(rateData.as_at);
                                const asAtTime = asAtDate.getTime();

                                // Find the surrounding time points
                                let nextIndex = rateData.latest.findIndex(rate =>
                                    new Date(rate.valid_from).getTime() > asAtTime
                                );
                                if (nextIndex === -1) nextIndex = rateData.latest.length;
                                const prevIndex = nextIndex - 1;

                                if (prevIndex < 0) return 0;  // Before first point
                                if (nextIndex >= rateData.latest.length) return rateData.latest.length - 1;  // After last point

                                // Calculate interpolation
                                const prevTime = new Date(rateData.latest[prevIndex].valid_from).getTime();
                                const nextTime = new Date(rateData.latest[nextIndex].valid_from).getTime();
                                const fraction = (asAtTime - prevTime) / (nextTime - prevTime);

                                // Return interpolated position
                                return prevIndex + fraction;
                            },
                            borderColor: 'red',
                            borderWidth: 2,
                            label: {
                                display: true,
                                content: 'Time: ' + new Date(rateData.as_at).toLocaleTimeString([],
                                    { hour: '2-digit', minute: '2-digit' }) +
                                    (rateData.current ? ' Price: ' + rateData.current.value_inc_vat.toFixed(2) + 'p/kWh' : ''),
                                position: 'top'
                            }
                        },
                        ...generateHeatingAnnotations(heatingData, rateData)
                    }
                }
            }
        }
    });
    console.log('Chart created successfully');
    console.log('Chart instance:', window.rateChart);
}

// Function to format date string
function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

// Function to generate heating periods for background fill
function generateHeatingPeriods(heatingData, rateData) {
    const periods = [];

    if (!heatingData.transitions || !rateData.latest) {
        return periods;
    }

    let currentHeatingState = false;
    let periodStart = null;

    // Create a map of heating states for each time slot
    const heatingStates = new Map();

    heatingData.transitions.forEach(transition => {
        const transitionTime = new Date(transition.time);
        const transitionTimeMs = transitionTime.getTime();

        // Find the index in rateData.latest that corresponds to this transition
        let rateIndex = rateData.latest.findIndex(rate => {
            const rateTime = new Date(rate.valid_from).getTime();
            return rateTime >= transitionTimeMs;
        });

        if (rateIndex === -1) rateIndex = rateData.latest.length - 1;

        // Set heating state for this time and all subsequent times until next transition
        for (let i = rateIndex; i < rateData.latest.length; i++) {
            heatingStates.set(i, transition.on);
        }
    });

    // Create background fill datasets for heating periods
    let currentPeriod = null;
    for (let i = 0; i < rateData.latest.length; i++) {
        const isHeating = heatingStates.get(i) || false;

        if (isHeating && !currentPeriod) {
            // Start of heating period
            currentPeriod = {
                label: '',
                data: new Array(rateData.latest.length).fill(null),
                backgroundColor: 'rgba(40, 167, 69, 0.12)', // Very light green background
                borderColor: 'rgba(40, 167, 69, 0.2)',
                borderWidth: 0,
                fill: 'origin',
                pointRadius: 0,
                pointHoverRadius: 0,
                tension: 0,
                stepped: 'before',
                showLine: false, // Hide the line, only show fill
                hidden: true, // Completely hide from legend
                legend: false // Exclude from legend completely
            };
        } else if (!isHeating && currentPeriod) {
            // End of heating period
            periods.push(currentPeriod);
            currentPeriod = null;
        }

        if (currentPeriod) {
            currentPeriod.data[i] = rateData.latest[i].value_inc_vat;
        }
    }

    // Add final period if it ends with heating
    if (currentPeriod) {
        periods.push(currentPeriod);
    }

    return periods;
}

// Function to generate heating schedule annotations
function generateHeatingAnnotations(heatingData, rateData) {
    const annotations = {};

    if (!heatingData.transitions || !rateData.latest) {
        return annotations;
    }

    heatingData.transitions.forEach((transition, index) => {
        const transitionTime = new Date(transition.time);
        const transitionTimeMs = transitionTime.getTime();

        // Find the index in rateData.latest that corresponds to this transition
        let rateIndex = rateData.latest.findIndex(rate => {
            const rateTime = new Date(rate.valid_from).getTime();
            return rateTime >= transitionTimeMs;
        });

        if (rateIndex === -1) rateIndex = rateData.latest.length - 1;

        const annotationKey = `heating_${index}`;
        annotations[annotationKey] = {
            type: 'line',
            scaleID: 'x',
            value: rateIndex,
            borderColor: transition.on ? '#28a745' : '#dc3545',
            borderWidth: 1,
            borderDash: transition.on ? [] : [3, 3],
            label: {
                display: transition.on, // Only show labels for Heating ON
                content: transition.on ? transition.price.toFixed(2) + 'p' : '',
                position: 'end',
                backgroundColor: transition.on ? '#28a745' : 'transparent',
                color: 'white',
                font: {
                    size: 9,
                    weight: 'bold'
                }
            }
        };
    });

    return annotations;
}

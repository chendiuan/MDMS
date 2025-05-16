// Utility functions for Electrical Validation Dashboard

// Function to update table content
function updateTable(tabId, data) {
    const tableBody = document.getElementById(`${tabId}Table`);
    tableBody.innerHTML = '';
    data.forEach(item => {
        let row;
        if (tabId === 'overview') {
            row = `
                <tr>
                    <td class="p-3">${item.test_id}</td>
                    <td class="p-3">${item.date}</td>
                    <td class="p-3">${item.metric}</td>
                    <td class="p-3">${item.value}</td>
                    <td class="p-3"><span class="status-badge ${item.status.toLowerCase()}">${item.status}</span></td>
                </tr>
            `;
        } else if (tabId === 'metrics') {
            row = `
                <tr>
                    <td class="p-3">${item.test_id}</td>
                    <td class="p-3">${item.date}</td>
                    <td class="p-3">${item.metric_type}</td>
                    <td class="p-3">${item.value}</td>
                    <td class="p-3">${item.threshold}</td>
                    <td class="p-3"><span class="status-badge ${item.status.toLowerCase()}">${item.status}</span></td>
                </tr>
            `;
        } else if (tabId === 'errors') {
            row = `
                <tr>
                    <td class="p-3">${item.test_id}</td>
                    <td class="p-3">${item.date}</td>
                    <td class="p-3">${item.error_code}</td>
                    <td class="p-3">${item.description}</td>
                    <td class="p-3"><span class="severity-badge ${item.severity.toLowerCase()}">${item.severity}</span></td>
                </tr>
            `;
        }
        tableBody.innerHTML += row;
    });
}

// Function to toggle search clear buttons
function toggleSearchClearButtons() {
    const searchInputs = {
        project: document.getElementById('projectSearch'),
        overview: document.getElementById('overviewSearch'),
        metrics: document.getElementById('metricsSearch'),
        errors: document.getElementById('errorsSearch')
    };

    Object.keys(searchInputs).forEach(id => {
        const input = searchInputs[id];
        const clearButton = document.getElementById(`${id}SearchClear`);
        clearButton.classList.toggle('hidden', !input.value);
    });
}
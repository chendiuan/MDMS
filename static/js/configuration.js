// Fetch JSON data for a specific project
async function loadConfigData(projectPath) {
    try {
        const response = await fetch(`reports/${projectPath}/config.json`);
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return await response.json();
    } catch (error) {
        console.error(`Error loading configuration data for ${projectPath}:`, error);
        return {};
    }
}

// Render BBFV Margins Table
function renderBBFVTable(container, data) {
    container.innerHTML = ''; // Clear previous content
    const table = document.createElement('table');
    table.className = 'config-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Parameter</th>
                <th>Value</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>BBFV IO Margin</td>
                <td>${data.BBFV_IO_Margin || ''}</td>
            </tr>
            <tr>
                <td>BBFV DDR Margin</td>
                <td>${data.BBFV_DDR_Margin || ''}</td>
            </tr>
        </tbody>
    `;
    container.appendChild(table);
}

// Render System Configuration Table
function renderSystemTable(container, data, projectPath) {
    container.innerHTML = ''; // Clear previous content
    const table = document.createElement('table');
    table.className = 'config-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>Risk</th>
                <th>Worst EHxEW</th>
                <th>End Device</th>
                <th>Source</th>
                <th>MCIO Cable</th>
                <th>AWG</th>
                <th>Length</th>
                <th>Loss</th>
                <th>To</th>
                <th>Slot</th>
                <th>Result</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    const tbody = table.querySelector('tbody');
    data.forEach(device => {
        device.rows.forEach((row, index) => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${row.risk}</td>
                <td>${row.worst_ehxew}</td>
                ${index === 0 ? `<td rowspan="${device.rows.length}">${device.end_device}</td>` : ''}
                <td>${row.source}</td>
                <td>${row.mcio_cable}</td>
                <td>${row.awg}</td>
                <td>${row.length}</td>
                <td>${row.loss}</td>
                <td>${row.to}</td>
                <td>${row.slot}</td>
                <td>${row.result ? `<a href="reports/${projectPath}/report.html" class="result-link">Report</a>` : ''}</td>
            `;
            tbody.appendChild(tr);
        });
    });
    container.appendChild(table);
}

// Render DIMM Configuration Table
function renderDIMMTable(container, data, projectPath) {
    container.innerHTML = ''; // Clear previous content
    const table = document.createElement('table');
    table.className = 'config-table';
    table.innerHTML = `
        <thead>
            <tr>
                <th>DIMM Type</th>
                <th>Vendor</th>
                <th>Description</th>
                <th>PN</th>
                <th>1DPC</th>
                <th>2DPC</th>
            </tr>
        </thead>
        <tbody></tbody>
    `;
    const tbody = table.querySelector('tbody');
    data.forEach(dimm => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${dimm.id}</td>
            <td>${dimm.vendor}</td>
            <td>${dimm.description}</td>
            <td>${dimm.pn}</td>
            <td>${dimm['1dpc'] ? `<a href="reports/${projectPath}/report.html" class="result-link">Report</a>` : '---'}</td>
            <td>${dimm['2dpc'] ? `<a href="reports/${projectPath}/report.html" class="result-link">Report</a>` : '---'}</td>
        `;
        tbody.appendChild(tr);
    });
    container.appendChild(table);
}

// Render tables for a specific project
async function renderTables(projectPath, configData) {
    if (!projectPath) {
        console.warn('No project path provided');
        return;
    }
    // Ensure containers exist
    const bbfvContainer = document.getElementById('table-container-bbfv');
    const systemContainer = document.getElementById('table-container-system');
    const dimmContainer = document.getElementById('table-container-dimm');

    if (!bbfvContainer || !systemContainer || !dimmContainer) {
        console.error('One or more table containers not found');
        return;
    }

    // Render tables with provided configData
    renderBBFVTable(bbfvContainer, configData.bbfv_margins || {});
    renderSystemTable(systemContainer, configData.system_configuration || [], projectPath);
    renderDIMMTable(dimmContainer, configData.dimm_configuration || [], projectPath);
}

// Search Functionality
function initConfigurationSearch(context = document) {
    const configSearch = context.querySelector('#searchInput');
    if (!configSearch) {
        console.warn('Search input not found');
        return;
    }

    let timeout;
    configSearch.addEventListener('input', function () {
        clearTimeout(timeout);
        timeout = setTimeout(() => {
            const searchTerm = this.value.toLowerCase().trim();
            const tables = context.querySelectorAll('.config-table');
            let hasResults = false;

            tables.forEach(table => {
                const rows = table.querySelectorAll('tbody tr');
                rows.forEach(row => {
                    let rowText = '';
                    Array.from(row.cells).forEach(cell => {
                        rowText += cell.textContent.toLowerCase().trim() + ' ';
                    });
                    const isVisible = rowText.includes(searchTerm);
                    row.style.display = isVisible ? '' : 'none';
                    if (isVisible) hasResults = true;
                });

                const panel = table.closest('.configuration-section');
                const noResults = panel.querySelector('.no-results');
                if (noResults) noResults.remove();
                if (!hasResults && searchTerm) {
                    const message = document.createElement('p');
                    message.className = 'no-results';
                    message.textContent = 'No results found';
                    panel.appendChild(message);
                }
            });
        }, 300);
    });
}

// Restore Table for Sorting
function restoreTableForSorting(table) {
    const rows = table.querySelectorAll('tbody tr');
    let currentEndDevice = '';
    rows.forEach(row => {
        if (row.cells[1] && row.cells[1].hasAttribute('rowspan')) {
            currentEndDevice = row.cells[1].textContent.trim();
            row.cells[1].removeAttribute('rowspan');
        } else if (!row.cells[1] || row.cells[1].textContent.trim() === '') {
            const newCell = row.insertCell(1);
            newCell.textContent = currentEndDevice;
        }
    });
}

// Merge End Device Cells
function mergeEndDeviceCells(table) {
    const rows = table.querySelectorAll('tbody tr');
    let currentDevice = null;
    let startRow = null;
    let count = 0;

    rows.forEach(row => {
        const endDeviceCell = row.cells[1];
        const endDevice = endDeviceCell.textContent.trim();

        if (endDevice !== currentDevice) {
            if (count > 1 && startRow) {
                startRow.cells[1].setAttribute('rowspan', count);
                for (let i = startRow.rowIndex + 1; i < startRow.rowIndex + count; i++) {
                    rows[i - 1].deleteCell(1);
                }
            }
            currentDevice = endDevice;
            startRow = row;
            count = 1;
        } else {
            count++;
        }
    });

    if (count > 1 && startRow) {
        startRow.cells[1].setAttribute('rowspan', count);
        for (let i = startRow.rowIndex + 1; i < startRow.rowIndex + count; i++) {
            rows[i - 1].deleteCell(1);
        }
    }
}

// Table Sorting
function initTableSorting(context = document) {
    const tables = context.querySelectorAll('.config-table');
    tables.forEach(table => {
        const headers = table.querySelectorAll('th');
        headers.forEach((header, index) => {
            header.addEventListener('click', () => {
                const isAscending = header.getAttribute('aria-sort') !== 'ascending';
                headers.forEach(h => h.removeAttribute('aria-sort'));
                header.setAttribute('aria-sort', isAscending ? 'ascending' : 'descending');

                if (table.closest('#configuration')) {
                    restoreTableForSorting(table);
                }

                const rows = Array.from(table.querySelectorAll('tbody tr'));
                rows.sort((a, b) => {
                    let aText = a.cells[index].textContent.trim();
                    let bText = b.cells[index].textContent.trim();
                    if (['AWG', 'Length', 'Loss'].includes(header.textContent)) {
                        aText = parseFloat(aText) || 0;
                        bText = parseFloat(bText) || 0;
                        return isAscending ? aText - bText : bText - aText;
                    }
                    return isAscending ? aText.localeCompare(bText) : bText.localeCompare(aText);
                });

                const tbody = table.querySelector('tbody');
                tbody.innerHTML = '';
                rows.forEach(row => tbody.appendChild(row));

                if (table.closest('#configuration')) {
                    mergeEndDeviceCells(table);
                }
            });
        });
    });
}

// Initialize Configuration Features
function initConfiguration(context = document) {
    console.log('Initializing configuration for context:', context);
    initConfigurationSearch(context);
    initTableSorting(context);
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM fully loaded, initializing configuration');
    initConfiguration();
});
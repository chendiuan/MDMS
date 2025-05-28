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

/*
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
*/

// Table Sorting
function initTableSorting(context = document) {
    console.log('Initializing configuration for context:', context);
    initConfigurationSearch(context);
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

// Dynamically generate tabs based on JSON files in the report folder
async function generateDynamicTabs(projectPath) {
    const tabList = document.querySelector('.tablist');
    const container = document.getElementById('configuration');
    if (!tabList || !container) {
        console.error('Tab list or configuration container not found.');
        return;
    }

    try {
        const response = await fetch(`/reports/${projectPath}/`);
        if (!response.ok) throw new Error(`Failed to access project directory: ${response.statusText}`);
        const htmlText = await response.text();
        const parser = new DOMParser();
        const doc = parser.parseFromString(htmlText, 'text/html');
        const files = Array.from(doc.querySelectorAll('a'))
            .map(link => link.getAttribute('href'))
            .filter(file => file.endsWith('.json') && file !== 'config.json');

        // Clear existing
        tabList.innerHTML = '';
        container.innerHTML = '';

        files.forEach((file, index) => {
            const tabId = `dynamic-tab-${index}`;
            const panelId = `dynamic-panel-${index}`;
            // Normalize the title by replacing non-standard spaces with regular spaces
            const title = file.replace('.json', '').replace(/\u00A0/g, ' ');

            // Create tab
            const tab = document.createElement('div');
            tab.className = 'tab' + (index === 0 ? ' active' : '');
            tab.setAttribute('role', 'tab');
            tab.setAttribute('id', tabId);
            tab.setAttribute('aria-controls', panelId);
            tab.setAttribute('aria-selected', index === 0 ? 'true' : 'false');
            tab.innerText = title;
            tabList.appendChild(tab);

            // Create panel
            const panel = document.createElement('div');
            panel.className = 'tabpanel dynamic-tabpanel configuration-section';
            panel.setAttribute('id', panelId);
            panel.setAttribute('role', 'tabpanel');
            panel.setAttribute('aria-labelledby', tabId);
            if (index !== 0) panel.hidden = true;
            panel.innerHTML = `<p>Loading ${file}...</p>`;
            container.appendChild(panel);

            // Load content
            fetch(`/reports/${projectPath}/${file}`)
                .then(res => res.json())
                .then(json => {
                    const html = renderJsonAsTable(json);
                    panel.innerHTML = html || `<pre>${JSON.stringify(json, null, 2)}</pre>`;
                    initConfiguration(panel); // Initialize search and sorting for this panel
                })
                .catch(err => {
                    panel.innerHTML = `<p class="text-red-500">Failed to load ${file}</p>`;
                    console.error(`Error loading ${file}:`, err);
                });
        });

        // Handle tab switching
        tabList.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', () => {
                tabList.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                container.querySelectorAll('.tabpanel').forEach(p => p.hidden = true);
                tab.classList.add('active');
                const targetId = tab.getAttribute('aria-controls');
                const targetPanel = document.getElementById(targetId);
                if (targetPanel) targetPanel.hidden = false;
            });
        });

    } catch (error) {
        console.error('Error generating dynamic tabs:', error);
    }
}

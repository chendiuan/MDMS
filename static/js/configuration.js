// Tablist Functionality
function initTablist(context = document) {
  const tabs = context.querySelectorAll('.tablist .tab');
  const panels = context.querySelectorAll('.tabpanel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => {
        t.classList.remove('active');
        t.setAttribute('aria-selected', 'false');
      });
      panels.forEach(p => p.setAttribute('hidden', 'true'));

      tab.classList.add('active');
      tab.setAttribute('aria-selected', 'true');
      const panelId = tab.getAttribute('aria-controls');
      context.getElementById(panelId).removeAttribute('hidden');
    });
  });
}

// Search Functionality
function initConfigurationSearch(context = document) {
  const configSearch = context.querySelector('#searchInput');
  if (!configSearch) return;

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
          if (table.closest('#panel1') && (!row.cells[1] || row.cells[1].textContent.trim() === '')) {
            let prevRow = row.previousElementSibling;
            while (prevRow && (!prevRow.cells[1] || prevRow.cells[1].textContent.trim() === '')) {
              prevRow = prevRow.previousElementSibling;
            }
            if (prevRow && prevRow.cells[1]) {
              rowText += prevRow.cells[1].textContent.toLowerCase().trim() + ' ';
            }
          }
          const isVisible = rowText.includes(searchTerm);
          row.style.display = isVisible ? '' : 'none';
          if (isVisible) hasResults = true;
        });

        const panel = table.closest('.tabpanel');
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

        if (table.closest('#panel1')) {
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

        if (table.closest('#panel1')) {
          mergeEndDeviceCells(table);
        }
      });
    });
  });
}

// Initialize Configuration Features
function initConfiguration(context = document) {
  initTablist(context);
  initConfigurationSearch(context);
  initTableSorting(context);
}

// MutationObserver to detect configuration content loading
document.addEventListener('DOMContentLoaded', () => {
  const configSection = document.getElementById('configuration');
  const observer = new MutationObserver(() => {
    if (configSection.querySelector('.tablist-container')) {
      initConfiguration(configSection);
    }
  });
  observer.observe(configSection, { childList: true, subtree: true });
});
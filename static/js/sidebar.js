// Sidebar functionality for Electrical Validation Dashboard

async function loadProjectList() {
    const projectList = document.getElementById('projectList');
    projectList.innerHTML = ''; // Clear existing list

    try {
        // Fetch project folder names (use API or static file)
        const response = await fetch('/api/projects'); // Or '/data/projects.json'
        if (!response.ok) throw new Error('Failed to load project list');
        const projects = await response.json();

        // Generate project list items
        projects.forEach(project => {
            const li = document.createElement('li');
            li.innerHTML = `
                <a href="#" class="block py-2 px-4 rounded hover:bg-blue-700 project-item" data-project="${project}" onclick="loadProject('${project}')">${project}</a>
            `;
            projectList.appendChild(li);
        });

        // Initialize project search
        initializeProjectSearch();
    } catch (error) {
        console.error('Error loading project list:', error);
        projectList.innerHTML = '<li class="text-red-400 p-4">Failed to load projects</li>';
    }
}

function initializeProjectSearch() {
    const projectSearch = document.getElementById('projectSearch');
    const projectItems = document.querySelectorAll('.project-item');
    const projectSearchClear = document.getElementById('projectSearchClear');

    projectSearch.addEventListener('input', () => {
        const query = projectSearch.value.toLowerCase();
        projectItems.forEach(item => {
            const projectName = item.getAttribute('data-project').toLowerCase();
            item.parentElement.style.display = projectName.includes(query) ? '' : 'none';
        });
        toggleSearchClearButtons();
    });

    projectSearchClear.addEventListener('click', () => {
        projectSearch.value = '';
        projectSearch.dispatchEvent(new Event('input'));
    });
}

document.addEventListener('DOMContentLoaded', () => {
    // Load project list
    loadProjectList();

    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('-translate-x-full');
    });
});
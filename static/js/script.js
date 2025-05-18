// Global variables to track current project and brand
let currentProject = null;
let currentBrand = null;

// Load project list into accordion
async function loadProjectList() {
    const projectList = document.getElementById('projectList');
    projectList.innerHTML = '<p>Loading projects...</p>';
    try {
        const response = await fetch('/data/projects.json');
        if (!response.ok) throw new Error(`Failed to load project list: ${response.statusText}`);
        const projects = await response.json();

        const projectsByVendor = projects.reduce((acc, project) => {
            acc[project.vendor] = acc[project.vendor] || [];
            acc[project.vendor].push(project);
            return acc;
        }, {});

        projectList.innerHTML = '';
        Object.keys(projectsByVendor).forEach(vendor => {
            const vendorProjects = projectsByVendor[vendor];
            const accordionItem = document.createElement('div');
            accordionItem.className = 'accordion-item';
            accordionItem.innerHTML = `
                <button class="accordion-header flex justify-between items-center w-full p-3 rounded hover:bg-gray-600 transition-colors" aria-expanded="false">
                    <span>${vendor}</span>
                    <i class="fas fa-chevron-down transition-transform"></i>
                </button>
                <div class="accordion-content hidden max-h-0 overflow-hidden transition-all duration-300">
                    <ul class="project-list">
                        ${vendorProjects.map(project => `
                            <li>
                                <a href="#" class="project-link block p-2 rounded hover:bg-blue-600 transition-colors" data-project="${project.name || project}" data-brand="${vendor}">${project.name || project}</a>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
            projectList.appendChild(accordionItem);
        });

        document.querySelectorAll('.accordion-header').forEach(header => {
            header.addEventListener('click', function () {
                const content = this.nextElementSibling;
                const isExpanded = this.getAttribute('aria-expanded') === 'true';
                this.setAttribute('aria-expanded', !isExpanded);
                this.querySelector('i').classList.toggle('fa-chevron-down', !isExpanded);
                this.querySelector('i').classList.toggle('fa-chevron-up', isExpanded);
                if (isExpanded) {
                    content.classList.add('hidden');
                    content.style.maxHeight = '0';
                } else {
                    content.classList.remove('hidden');
                    content.style.maxHeight = content.scrollHeight + 'px';
                }
            });
        });

        document.querySelectorAll('.project-link').forEach(link => {
            link.addEventListener('click', function (e) {
                e.preventDefault();
                const brand = this.getAttribute('data-brand');
                const project = this.getAttribute('data-project');
                currentProject = project;
                currentBrand = brand;
                loadCurrentTabContent(); // Load content for the active tab
            });
        });

        initializeProjectSearch();
    } catch (error) {
        console.error('Error loading project list:', error);
        projectList.innerHTML = '<p class="text-red-400 p-4">Failed to load projects</p>';
    }
}

// Initialize sidebar search to filter accordion items
function initializeProjectSearch() {
    const projectSearch = document.getElementById('sidebarSearch');
    const projectSearchClear = document.getElementById('sidebarSearchClear');
    const projectList = document.getElementById('projectList');

    projectSearch.addEventListener('input', () => {
        const query = projectSearch.value.toLowerCase();
        const accordionItems = document.querySelectorAll('.accordion-item');
        let anyVisible = false;

        accordionItems.forEach(item => {
            const header = item.querySelector('.accordion-header');
            const content = item.querySelector('.accordion-content');
            const links = item.querySelectorAll('.project-link');
            let hasVisibleLinks = false;

            links.forEach(link => {
                const projectName = link.getAttribute('data-project').toLowerCase();
                const isVisible = projectName.includes(query);
                link.parentElement.style.display = isVisible ? '' : 'none';
                if (isVisible) hasVisibleLinks = true;
            });

            item.style.display = hasVisibleLinks || !query ? '' : 'none';
            if (hasVisibleLinks && query) {
                header.setAttribute('aria-expanded', 'true');
                header.querySelector('i').classList.remove('fa-chevron-down');
                header.querySelector('i').classList.add('fa-chevron-up');
                content.classList.remove('hidden');
                content.style.maxHeight = `${content.scrollHeight}px`;
                anyVisible = true;
            } else {
                header.setAttribute('aria-expanded', 'false');
                header.querySelector('i').classList.add('fa-chevron-down');
                header.querySelector('i').classList.remove('fa-chevron-up');
                content.classList.add('hidden');
                content.style.maxHeight = '0';
                anyVisible = !query;
            }
        });

        projectSearchClear.classList.toggle('hidden', !projectSearch.value);
        if (!anyVisible && query) {
            projectList.innerHTML = '<p class="text-red-400 p-4">No matching projects</p>';
        } else if (!anyVisible && !query) {
            projectList.innerHTML = '<p>Loading projects...</p>';
        }
    });

    projectSearchClear.addEventListener('click', () => {
        projectSearch.value = '';
        projectSearch.dispatchEvent(new Event('input'));
    });
}

// Load content for the currently active tab
async function loadCurrentTabContent() {
    if (!currentProject || !currentBrand) return;

    const activeTab = document.querySelector('.tab.active');
    if (!activeTab) return;

    const tabId = activeTab.getAttribute('data-tab');

    if (tabId === 'summary') {
        const summaryContent = document.getElementById('summary');
        try {
            const summaryResponse = await fetch(`/reports/${currentBrand}/${currentProject}/summary.html`);
            if (!summaryResponse.ok) throw new Error(`Failed to load summary.html: ${summaryResponse.statusText}`);
            const summaryHtml = await summaryResponse.text();
            summaryContent.innerHTML = summaryHtml;
        } catch (error) {
            console.error('Error loading summary:', error);
            summaryContent.innerHTML = `<p class="text-red-400 p-4">Failed to load summary for ${currentProject}. Error: ${error.message}</p>`;
        }
    } else if (tabId === 'configuration') {
        const configContent = document.getElementById('configuration-content');
        try {
            const configResponse = await fetch(`/reports/${currentBrand}/${currentProject}/configuration.html`);
            if (!configResponse.ok) throw new Error(`Failed to load configuration.html: ${configResponse.statusText}`);
            const configHtml = await configResponse.text();
            configContent.innerHTML = configHtml;

            // Reinitialize configuration features and force CSS refresh
            const configurationDiv = document.getElementById('configuration');
            initConfiguration(configurationDiv);
            // Force reflow to apply CSS
            configurationDiv.style.display = 'none';
            configurationDiv.offsetHeight; // Trigger reflow
            configurationDiv.style.display = '';
        } catch (error) {
            console.error('Error loading configuration:', error);
            configContent.innerHTML = `<p class="text-red-400 p-4">Failed to load configuration for ${currentProject}. Error: ${error.message}</p>`;
        }
    }
}

// Initialize theme toggle on page load
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    const savedTheme = localStorage.getItem('theme') || 'light';
    html.classList.toggle('dark-mode', savedTheme === 'dark');
    themeToggle.setAttribute('data-theme', savedTheme);
    themeToggle.innerHTML = savedTheme === 'light' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';

    themeToggle.addEventListener('click', () => {
        const currentTheme = themeToggle.getAttribute('data-theme');
        const newTheme = currentTheme === 'light' ? 'dark' : 'light';

        html.classList.toggle('dark-mode', newTheme === 'dark');
        themeToggle.setAttribute('data-theme', newTheme);
        themeToggle.innerHTML = newTheme === 'light' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';

        localStorage.setItem('theme', newTheme);
    });
}
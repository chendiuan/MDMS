// Global variables to track current project, brand, and config data
let currentProject = null;
let currentBrand = null;
let currentConfigData = null; // Store config data

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
                currentConfigData = null; // Reset config data
                const configSearch = document.querySelector('#searchInput');
                if (configSearch) {
                    configSearch.value = ''; // Clear search input
                    configSearch.dispatchEvent(new Event('input')); // Trigger search update
                }
                loadCurrentTabContent(); // Load configuration content
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

    if (projectSearch && projectSearchClear && projectList) {
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
    } else {
        console.warn('Sidebar search elements not found:', {
            projectSearch: !!projectSearch,
            projectSearchClear: !!projectSearchClear,
            projectList: !!projectList
        });
    }
}

// Load configuration content for the selected project
async function loadCurrentTabContent() {
    if (!currentProject || !currentBrand) return;

    const configContent = document.getElementById('configuration');
    if (configContent) {
        configContent.style.display = 'block';
        try {
            if (!currentConfigData) {
                const configResponse = await fetch(`/reports/${currentBrand}/${currentProject}/config.json`);
                if (!configResponse.ok) {
                    throw new Error(`Failed to load config.json: ${configResponse.statusText}`);
                }
                currentConfigData = await configResponse.json();
                console.log('Config data loaded:', currentConfigData); // Debug
            }
            renderTables(`${currentBrand}/${currentProject}`, currentConfigData);
        } catch (error) {
            console.error('Error loading configuration:', error);
            configContent.innerHTML = `<p class="text-red-400 p-4">Configuration data for ${currentProject} is not available. Please check the file or contact support.</p>`;
        }
    } else {
        console.warn('Configuration element not found in DOM');
    }
}

// Initialize theme toggle on page load
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const html = document.documentElement;

    if (themeToggle) {
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
    } else {
        console.warn('Theme toggle element not found in DOM');
    }
}

// Initialize navigation buttons and date/time display
function initializeNavigation() {
    // Home button
    const homeButton = document.getElementById('homeButton');
    if (homeButton) {
        homeButton.addEventListener('click', () => {
            window.location.href = '/index.html';
        });
    } else {
        console.warn('Home button not found in DOM');
    }

    // About button with jQuery
    $(document).ready(function () {
        const $aboutButton = $('#aboutButton');
        const $aboutModal = $('#aboutModal');
        const $closeAboutModal = $('#closeAboutModal');

        if ($aboutButton.length && $aboutModal.length && $closeAboutModal.length) {
            $aboutModal.addClass('hidden'); // Ensure modal is hidden on load
            $aboutButton.on('click', function () {
                console.log('About button clicked');
                $aboutModal.removeClass('hidden').fadeIn(300);
            });
            $closeAboutModal.on('click', function () {
                console.log('Close modal clicked');
                $aboutModal.fadeOut(300, function () {
                    $(this).addClass('hidden');
                });
            });
            $aboutModal.on('click', function (e) {
                if ($(e.target).is($aboutModal)) {
                    console.log('Clicked outside modal');
                    $aboutModal.fadeOut(300, function () {
                        $(this).addClass('hidden');
                    });
                }
            });
        } else {
            console.warn('About button or modal elements not found:', {
                aboutButton: $aboutButton.length,
                aboutModal: $aboutModal.length,
                closeAboutModal: $closeAboutModal.length
            });
        }
    });

    // Date and time display
    const dateTimeDisplay = document.getElementById('dateTimeDisplay');
    if (dateTimeDisplay) {
        function updateDateTime() {
            try {
                const now = new Date();
                const options = {
                    timeZone: 'America/Chicago',
                    weekday: 'long',
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: 'numeric',
                    second: 'numeric',
                    hour12: true
                };
                const formattedDateTime = now.toLocaleString('en-US', options);
                dateTimeDisplay.textContent = formattedDateTime;
            } catch (error) {
                console.error('Error updating date/time:', error);
                dateTimeDisplay.textContent = 'Unable to display time';
            }
        }

        // Update immediately and every second
        updateDateTime();
        setInterval(updateDateTime, 1000);
    } else {
        console.warn('dateTimeDisplay element not found in DOM');
    }
}

// Call initialization functions on page load
document.addEventListener('DOMContentLoaded', () => {
    // Ensure modal is hidden on page load
    const aboutModal = document.getElementById('aboutModal');
    if (aboutModal) {
        aboutModal.classList.add('hidden');
    }
    loadProjectList();
    initializeThemeToggle();
    loadCurrentTabContent();
    initializeNavigation(); // Initialize navigation buttons and date/time
});
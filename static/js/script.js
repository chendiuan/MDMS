$(document).ready(function () {
    // Global variable to store project data
    let projects = [];

    // Load project list into accordion
    async function loadProjectList() {
        const projectList = document.getElementById('projectList');
        projectList.innerHTML = '';
        try {
            const response = await fetch('data/projects.json');
            if (!response.ok) throw new Error('Failed to load project list');
            projects = await response.json();

            // Group projects by vendor
            const projectsByVendor = projects.reduce((acc, project) => {
                acc[project.vendor] = acc[project.vendor] || [];
                acc[project.vendor].push(project);
                return acc;
            }, {});

            // Generate accordion for each vendor (default collapsed)
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
                                    <a href="#" class="project-link block p-2 rounded hover:bg-blue-600 transition-colors" data-project="${project.name}" data-brand="${project.vendor}">${project.name}</a>
                                </li>
                            `).join('')}
                        </ul>
                    </div>
                `;
                projectList.appendChild(accordionItem);
            });

            // Bind accordion toggle events
            $('.accordion-header').on('click', function () {
                const $header = $(this);
                const $content = $header.next('.accordion-content');
                const isExpanded = $header.attr('aria-expanded') === 'true';
                $header.attr('aria-expanded', !isExpanded);
                $header.find('i').toggleClass('fa-chevron-down fa-chevron-up');
                if (isExpanded) {
                    $content.addClass('hidden');
                    $content.css('max-height', '0');
                } else {
                    $content.removeClass('hidden');
                    $content.css('max-height', $content[0].scrollHeight + 'px');
                }
                console.log(`Accordion ${$header.find('span').text()} max-height: ${$content.css('max-height')}`);
            });

            // Bind project link clicks
            $('.project-link').on('click', function (e) {
                e.preventDefault();
                const brand = $(this).data('brand');
                const project = $(this).data('project');
                loadProject(project, brand);
            });

            initializeProjectSearch();

            // Debug: Check styles
            console.log('Sidebar background:', $('#sidebar').css('background'));
            console.log('Accordion header background:', $('.accordion-header').css('background-color'));
        } catch (error) {
            console.error('Error loading project list:', error);
            projectList.innerHTML = '<p class="text-red-400 p-4">Failed to load projects</p>';
        }
    }

    // Initialize sidebar search to filter accordion items
    function initializeProjectSearch() {
        const projectSearch = document.getElementById('sidebarSearch');
        const projectSearchClear = document.getElementById('sidebarSearchClear');
        const projectLinks = document.querySelectorAll('.project-link');
        const accordionItems = document.querySelectorAll('.accordion-item');

        projectSearch.addEventListener('input', () => {
            const query = projectSearch.value.toLowerCase();
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
                } else if (!query) {
                    header.setAttribute('aria-expanded', 'false');
                    header.querySelector('i').classList.add('fa-chevron-down');
                    header.querySelector('i').classList.remove('fa-chevron-up');
                    content.classList.add('hidden');
                    content.style.maxHeight = '0';
                    anyVisible = true;
                }
            });

            projectSearchClear.classList.toggle('hidden', !projectSearch.value);
            projectList.innerHTML = anyVisible ? projectList.innerHTML : '<p class="text-red-400 p-4">No matching projects</p>';
        });

        projectSearchClear.addEventListener('click', () => {
            projectSearch.value = '';
            projectSearch.dispatchEvent(new Event('input'));
        });
    }

    // Load specific project
    function loadProject(projectName, brand) {
        const project = projects.find(p => p.name === projectName && p.vendor === brand);
        if (project) {
            $('#project-title').text(project.name);
            loadContent(`reports/${project.vendor}/${project.name}/summary.html`, 'summary');
            loadConfiguration(project.vendor, project.name).then(() => {
                $('#tab-configuration').show();
                openTab('configuration');
            });
        }
    }

    // Switch tabs
    function openTab(tabId) {
        $('.tab-content').removeClass('active').hide();
        $('.tabs .tab').removeClass('active').attr('aria-selected', 'false');
        $(`#${tabId}`).addClass('active').show();
        $(`#tab-${tabId}`).addClass('active').attr('aria-selected', 'true');
    }

    // Update tab visibility
    function updateTabs() {
        const title = $('#project-title').text();
        const $configTab = $('#tab-configuration');
        if (title === 'Dashboard') {
            $configTab.hide();
            $('#configuration').hide();
            openTab('summary');
        } else {
            $configTab.show();
        }
    }

    // Load content
    function loadContent(url, elementId) {
        const $element = $(`#${elementId}`);
        $element.html('<div class="loading">Loading...</div>');
        return $.ajax({
            url: url,
            method: 'GET'
        }).then(data => {
            $element.html(data);
        }).catch(err => {
            console.error(`Error loading ${elementId} content:`, err);
            $element.html(`<p>Failed to load ${elementId}. Please check the file path or server.</p>`);
        });
    }

    // Load configuration tab
    function loadConfiguration(brand, project) {
        const $configSection = $('#configuration');
        $configSection.html('<div class="loading">Loading configuration...</div>');

        console.log(`Attempting to load configuration for ${brand}/${project} from reports/${brand}/${project}/config.json`);

        return $.ajax({
            url: `reports/${brand}/${project}/config.json?v=${Date.now()}`,
            method: 'GET'
        }).then(data => {
            console.log('Configuration data loaded successfully:', data);
            $configSection.empty();
            const $container = $('<div class="tablist-container"></div>');
            data.tablists.forEach(tablist => {
                console.log(`Processing tablist: ${tablist.title}`);

                const $tablist = $(`
                    <div class="config-tablist" data-tablist="${tablist.id}">
                        <h3>${tablist.title}</h3>
                        <nav class="sub-tabs" role="tablist"></nav>
                        <div class="sub-tab-content"></div>
                    </div>
                `);
                const $subTabs = $tablist.find('.sub-tabs');
                const $subContent = $tablist.find('.sub-tab-content');

                tablist.tabs.forEach((tab, index) => {
                    console.log(`Processing tab: ${tab.title} with content length: ${tab.content ? tab.content.length : 0}`);

                    const isActive = index === 0 ? 'active' : '';
                    const ariaSelected = index === 0 ? 'true' : 'false';
                    $subTabs.append(`
                        <button class="sub-tab ${isActive}" role="tab" aria-selected="${ariaSelected}" aria-controls="${tab.id}" data-tab="${tab.id}">
                            ${tab.title}
                        </button>
                    `);

                    let contentHtml = '';
                    if (tab.content && tab.content.length > 0) {
                        console.log(`Rendering table for ${tab.title} with ${tab.content.length} rows`);

                        let tableHtml = '<table class="config-table"><thead><tr>';
                        const headers = Object.keys(tab.content[0]);
                        headers.forEach(header => {
                            tableHtml += `<th>${header.replace(/_/g, ' ').toUpperCase()}</th>`;
                        });
                        tableHtml += '</tr></thead><tbody>';
                        tab.content.forEach(row => {
                            tableHtml += '<tr>';
                            headers.forEach(header => {
                                const value = row[header];
                                if (header === 'result' || header === '1dpc' || header === '2dpc') {
                                    tableHtml += `<td>${value ? `<a href="${value}" class="result-link" target="_blank">Report</a>` : '—'}</td>`;
                                } else {
                                    tableHtml += `<td>${value || '—'}</td>`;
                                }
                            });
                            tableHtml += '</tr>';
                        });
                        tableHtml += '</tbody></table>';
                        contentHtml = tableHtml;
                    } else {
                        console.log(`No data for ${tab.title}, showing placeholder message`);
                        contentHtml = '<p>No data available for this category.</p>';
                    }

                    $subContent.append(`
                        <div class="sub-tab-content ${isActive}" id="${tab.id}" role="tabpanel" aria-labelledby="${tab.id}">
                            ${contentHtml}
                        </div>
                    `);
                    console.log(`Rendered HTML for ${tab.title}:`, $(`#${tab.id}`).html());
                });

                $container.append($tablist);
            });
            $configSection.append($container);
            console.log('Final configuration section HTML:', $configSection.html());

            $('.sub-tab').on('click', function () {
                const $tablist = $(this).closest('.config-tablist');
                $tablist.find('.sub-tab').removeClass('active').attr('aria-selected', 'false');
                $tablist.find('.sub-tab-content').removeClass('active').hide();
                $(this).addClass('active').attr('aria-selected', 'true');
                $(`#${$(this).data('tab')}`).addClass('active').show();
                console.log(`Switched to tab: ${$(this).data('tab')}`);
            });
        }).catch(err => {
            console.error('Error loading configuration:', err);
            $configSection.html('<p>Failed to load configuration data. Please check the file path.</p>');
        });
    }

    // Tab switching
    $('.tabs .tab').on('click', function () {
        const tabId = $(this).attr('aria-controls');
        openTab(tabId);
    });

    // Expand/collapse submenu
    $('.toggle-submenu').on('click', function (e) {
        e.preventDefault();
        const $parent = $(this).closest('.parent-item');
        const isActive = $parent.toggleClass('active').hasClass('active');
        $(this).attr('aria-expanded', isActive);
    });

    // Load homepage summary
    loadContent('summary.html', 'summary').then(updateTabs);

    // Home button
    $('#home-link').on('click', function (e) {
        e.preventDefault();
        $('#project-title').text('Dashboard');
        loadContent('summary.html', 'summary').then(updateTabs);
    });

    // Theme toggle
    const $themeToggle = $('#themeToggle');
    if (localStorage.getItem('theme') === 'dark') {
        $('html').addClass('dark-mode');
        $themeToggle.html('<i class="fas fa-sun"></i>');
    }

    $themeToggle.on('click', function () {
        $('html').toggleClass('dark-mode');
        const isDark = $('html').hasClass('dark-mode');
        $(this).html(isDark ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>');
        localStorage.setItem('theme', isDark ? 'dark' : 'light');
    });

    // Time display
    function updateTime() {
        const now = new Date();
        $('#currentTime').text(`Current Time: ${now.toLocaleTimeString('en-US')}`);
    }
    updateTime();
    setInterval(updateTime, 1000);

    // Back to top
    const $backToTop = $('#backToTop');
    $(window).on('scroll', function () {
        $backToTop.toggleClass('visible', $(window).scrollTop() > 300);
    });

    $backToTop.on('click', function () {
        $('html, body').animate({ scrollTop: 0 }, 'smooth');
    });

    // Initialize project list
    loadProjectList();

    // Sidebar toggle for mobile
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('active');
    });
});
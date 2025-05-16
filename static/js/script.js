$(document).ready(function () {
  // Utility function to switch tabs
  function openTab(tabId) {
    $('.tab-content').removeClass('active').hide();
    $('.tabs .tab').removeClass('active').attr('aria-selected', 'false');
    $(`#${tabId}`).addClass('active').show();
    $(`#tab-${tabId}`).addClass('active').attr('aria-selected', 'true');
  }

  // Utility function: Update tab visibility
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

  // Utility function to load content
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

  // Utility function to load configuration tablists
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

          // Generate table from content array, or show a message if content is empty
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

          // Log the rendered HTML to verify
          console.log(`Rendered HTML for ${tab.title}:`, $(`#${tab.id}`).html());
        });

        $container.append($tablist);
      });
      $configSection.append($container);

      // Log the final HTML of the configuration section
      console.log('Final configuration section HTML:', $configSection.html());

      // Bind sub-tab click events
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

  // Project links
  $('.project-link').on('click', function (e) {
    e.preventDefault();
    const brand = $(this).data('brand');
    const project = $(this).data('project');
    $('#project-title').text(project);

    // Load summary content (non-blocking)
    loadContent(`reports/${brand}/${project}/summary.html`, 'summary');

    // Load configuration independently
    loadConfiguration(brand, project).then(() => {
      $('#tab-configuration').show();
      openTab('configuration');
    });
  });

  // Sidebar search
  $('#sidebarSearch').on('input', function () {
    const searchTerm = $(this).val().toLowerCase();
    $('.project-link').each(function () {
      const projectName = $(this).text().toLowerCase();
      const $parentItem = $(this).closest('.parent-item');
      const $submenu = $parentItem.find('.submenu');
      const $toggle = $parentItem.find('.toggle-submenu');

      if (projectName.includes(searchTerm)) {
        $(this).show();
        $parentItem.addClass('active');
        $toggle.attr('aria-expanded', 'true');
        $submenu.css({ maxHeight: '500px', opacity: '1' });
      } else {
        $(this).hide();
      }

      const $visibleLinks = $submenu.find('a').filter(function () {
        return $(this).css('display') !== 'none';
      });
      if ($visibleLinks.length === 0) {
        $parentItem.removeClass('active');
        $toggle.attr('aria-expanded', 'false');
        $submenu.css({ maxHeight: '0', opacity: '0' });
      }
    });
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
    $('#currentTime').text(`Current Time: ${now.toLocaleTimeString()}`);
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
});
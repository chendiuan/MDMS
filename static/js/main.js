setInterval(()=>{ 
    document.getElementById('currentDateTime').innerText = new Date().toLocaleString(); 
}, 1000);

async function loadProjects() {
    const resp = await fetch('/api/projects');
    const data = await resp.json();
    let byVendor = {};
    data.forEach(proj=>{
        if(!byVendor[proj.vendor]) byVendor[proj.vendor]=[];
        byVendor[proj.vendor].push(proj.name);
    });
    let html = '';
    for(const vendor in byVendor){
        html += `
        <div class="accordion-item">
            <div class="accordion-header" tabindex="0">
                <span>${vendor}</span>
                <span class="chevron">&#9654;</span>
            </div>
            <div class="accordion-content">
                <ul class="project-list">
                    ${byVendor[vendor].map(p=>`
                        <li>
                            <a href="#" class="project-link" data-vendor="${vendor}" data-project="${p}">${p}</a>
                        </li>
                    `).join('')}
                </ul>
            </div>
        </div>`;
    }
    $('#projectList').html(html);

    // 展開/收合
    $('.accordion-header').on('click keydown', function(e){
        if(e.type==='click' || (e.type==='keydown' && (e.key==='Enter'||e.key===' '))){
            let $header = $(this);
            let $content = $header.next('.accordion-content');
            let open = $content.hasClass('open');
            $('.accordion-content').removeClass('open');
            $('.accordion-header').removeClass('open');
            if(!open){
                $header.addClass('open');
                $content.addClass('open');
            }
        }
    });

    // project 點擊
    $('.project-link').on('click', function(e){
        e.preventDefault();
        $('.project-link').removeClass('active');
        $(this).addClass('active');
        loadProjectReport($(this).data('vendor'), $(this).data('project'));
    });
}
loadProjects();

async function loadProjectReport(vendor, project){
    $('#mainContent').html('<h3>Loading...</h3>');
    const resp = await fetch(`/api/reports/${vendor}/${project}`); 
    const files = await resp.json();
    if(!files.length) { 
        $('#mainContent').html('<p>No report JSON found.</p>'); 
        return; 
    }
    let tabHtml = `<div class="tablist" role="tablist">`;
    let panelHtml = ``;
    files.forEach((fname,i)=>{
        let tabid = `tab${i}`;
        tabHtml += `<div class="tab${i==0?' active':''}" data-tab="${tabid}" role="tab" tabindex="0">${fname.replace('.json','')}</div>`;
        panelHtml += `<section class="tabpanel${i==0?' active':''}" id="${tabid}"><div>Loading...</div></section>`;
    });
    tabHtml += `</div>`;
    $('#mainContent').html(tabHtml+panelHtml);

    // 載入每個 json 成表格
    files.forEach((fname,i)=>{
        fetch(`/api/report_json/${vendor}/${project}/${fname}`).then(r=>r.json()).then(json=>{
            $(`#tab${i}`).html(renderJsonTable(json));
        });
    });

    // tab 切換
    $('.tab').on('click keydown', function(e){
        if(e.type==='click'||(e.type==='keydown'&&(e.key==='Enter'||e.key===' '))){
            $('.tab').removeClass('active'); 
            $(this).addClass('active');
            $('.tabpanel').removeClass('active').hide();
            $('#'+$(this).data('tab')).addClass('active').show();
        }
    });

    // 初始只顯示第一個 panel
    $('.tabpanel').not('.active').hide();
}

function renderJsonTable(json){
    if(!json.tablists) return "<pre>"+JSON.stringify(json,null,2)+"</pre>";
    let html = "";
    json.tablists.forEach(tablist=>{
        tablist.tabs.forEach(tab=>{
            let content = tab.content;
            if(!Array.isArray(content) || content.length==0) return;
            let headers = Object.keys(content[0]);
            html += `<table class="config-table"><thead><tr>${headers.map(h=>`<th>${h}</th>`).join('')}</tr></thead><tbody>`;
            content.forEach(row=>{
                html += "<tr>"+headers.map(h=>`<td>${row[h]||""}</td>`).join('')+"</tr>";
            });
            html += "</tbody></table>";
        });
    });
    return html;
}

// 點選Report Generate
$('#reportGenerateBtn').click(function(){
    $('.project-link').removeClass('active');
    let tpl = document.getElementById('reportGeneratePanel').content.cloneNode(true);
    $('#mainContent').html(tpl);
    loadScriptList();
    // 綁定送出
    $('#generateForm').submit(async function(e){
        e.preventDefault();
        let formData = new FormData(this);
        $('#generateResult').html('Generating...');
        const resp = await fetch('/api/generate_report',{method:'POST',body:formData});
        if(resp.ok){
            const blob = await resp.blob();
            const url = window.URL.createObjectURL(blob);
            $('#generateResult').html(`<a href="${url}" download="report.html" class="nav-button" style="margin-top:1rem;">Download Report</a>`);
        }else{
            const err = await resp.text();
            $('#generateResult').html('<span style="color:red;">Error: '+err+'</span>');
        }
    });
});
async function loadScriptList(){
    const resp = await fetch('/api/scripts'); 
    const scripts = await resp.json();
    $('#scriptSelect').html(scripts.map(s=>`<option value="${s}">${s}</option>`).join(''));
}

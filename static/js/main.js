// Gerenciamento do título dinâmico
function updatePageTitle(section) {
    const titles = {
        'acordo': 'Gestão de Acordos - DataAnalytics SAAS',
        'diario': 'Relatório Diário - DataAnalytics SAAS',
        'geral': 'Relatório Geral - DataAnalytics SAAS'
    };
    document.title = titles[section] || 'DataAnalytics SAAS';
}

// Inicialização dos gráficos
function initCharts() {
    // Gráfico de Status
    const statusData = {
        values: [30, 20, 15, 35],
        labels: ['PENDENTE', 'VERIFICADO', 'ANÁLISE', 'PRIORIDADE'],
        type: 'pie'
    };

    const statusLayout = {
        height: 300,
        margin: { t: 0, b: 0, l: 0, r: 0 }
    };

    Plotly.newPlot('statusChart', [statusData], statusLayout);

    // Gráfico de Timeline
    const timelineData = {
        x: ['Jan', 'Fev', 'Mar', 'Abr', 'Mai'],
        y: [20, 35, 45, 30, 50],
        type: 'scatter'
    };

    const timelineLayout = {
        height: 300,
        margin: { t: 20, b: 40, l: 40, r: 20 }
    };

    Plotly.newPlot('timelineChart', [timelineData], timelineLayout);
}

// Atualização dos KPIs
function updateKPIs(data) {
    document.getElementById('totalCases').textContent = data.total || '0';
    document.getElementById('pendingCases').textContent = data.pending || '0';
    document.getElementById('resolvedCases').textContent = data.resolved || '0';
    document.getElementById('resolutionRate').textContent = `${data.rate || 0}%`;
}

// Atualização da tabela
function updateTable(data) {
    const tbody = document.querySelector('#dataTable tbody');
    tbody.innerHTML = '';

    data.forEach(row => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.id}</td>
            <td>${row.date}</td>
            <td><span class="status-${row.status.toLowerCase()}">${row.status}</span></td>
            <td>${row.group}</td>
            <td>${row.responsible}</td>
            <td>${row.resolution_time}</td>
        `;
        tbody.appendChild(tr);
    });
}

// Manipulação dos filtros
document.getElementById('filterForm').addEventListener('submit', function(e) {
    e.preventDefault();
    const filters = {
        group: document.getElementById('groupSelect').value,
        status: Array.from(document.getElementById('statusSelect').selectedOptions).map(opt => opt.value),
        startDate: document.getElementById('startDate').value,
        endDate: document.getElementById('endDate').value
    };

    // Fazer requisição para o backend com os filtros
    fetchData(filters);
});

// Função para buscar dados do backend
async function fetchData(filters) {
    try {
        const response = await fetch('/api/data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(filters)
        });

        if (!response.ok) throw new Error('Erro ao buscar dados');

        const data = await response.json();
        updateKPIs(data.kpis);
        updateTable(data.table);
        updateCharts(data.charts);
    } catch (error) {
        console.error('Erro:', error);
        alert('Erro ao carregar dados. Por favor, tente novamente.');
    }
}

// Event Listeners para navegação
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', function(e) {
        e.preventDefault();
        const section = this.dataset.section;
        updatePageTitle(section);
        // Adicionar lógica para carregar dados específicos da seção
    });
});

// Inicialização
document.addEventListener('DOMContentLoaded', function() {
    initCharts();
    // Carregar dados iniciais
    fetchData({});
});

// Estado de la aplicación
let state = {
    currentBloque: 'todos',
    editoriales: [],
    filteredEditoriales: [],
    searchTerm: '',
    filterEstado: ''
};

// Inicialización
document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
    loadStats();
    loadEditoriales();
});

function initEventListeners() {
    // Tabs
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const bloque = e.target.dataset.bloque;
            switchTab(bloque);
        });
    });

    // Búsqueda
    const searchInput = document.getElementById('search-input');
    const btnClearSearch = document.getElementById('btn-clear-search');
    
    searchInput.addEventListener('input', (e) => {
        state.searchTerm = e.target.value.toLowerCase();
        
        // Mostrar/ocultar botón limpiar
        if (e.target.value) {
            btnClearSearch.style.display = 'block';
        } else {
            btnClearSearch.style.display = 'none';
        }
        
        filterAndRender();
    });
    
    btnClearSearch.addEventListener('click', () => {
        searchInput.value = '';
        state.searchTerm = '';
        btnClearSearch.style.display = 'none';
        filterAndRender();
    });

    // Filtro de estado
    document.getElementById('filter-estado').addEventListener('change', (e) => {
        state.filterEstado = e.target.value;
        filterAndRender();
    });

    // Normalizar orden
    document.getElementById('btn-normalizar').addEventListener('click', () => {
        if (state.currentBloque !== 'todos') {
            normalizarOrden(state.currentBloque);
        } else {
            alert('Selecciona un bloque específico para normalizar');
        }
    });

    // Analizar todas con IA
    document.getElementById('btn-analizar-todas').addEventListener('click', analizarTodas);

    // Configuración
    document.getElementById('btn-config').addEventListener('click', abrirModalConfig);

    // Modals - cerrar al hacer click fuera
    window.addEventListener('click', (e) => {
        if (e.target.id === 'modal-detalle') {
            closeModalDetalle();
        }
        if (e.target.id === 'modal-editar') {
            closeModalEditar();
        }
        if (e.target.id === 'modal-analisis-progreso') {
            // No cerrar automáticamente durante análisis
        }
        if (e.target.id === 'modal-config') {
            closeModalConfig();
        }
    });
    
    // Verificar disponibilidad de IA al cargar
    verificarIADisponible();
}

// Cargar estadísticas
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        
        const statsBar = document.getElementById('stats-bar');
        statsBar.innerHTML = `
            <span><strong>Total:</strong> ${stats.total} editoriales</span>
            <span><strong>Con análisis IA:</strong> ${stats.con_analisis_ia || 0}</span>
            <span><strong>Pendientes:</strong> ${stats.por_estado?.pendiente || 0}</span>
            <span><strong>En proceso:</strong> ${stats.por_estado?.['en-proceso'] || 0}</span>
            <span><strong>En evaluación:</strong> ${stats.por_estado?.['en-evaluacion'] || 0}</span>
            <span><strong>Finalizadas:</strong> ${stats.por_estado?.finalizado || 0}</span>
        `;
        
        // Actualizar badges de bloques
        ['A', 'B', 'C', 'D'].forEach(bloque => {
            const badge = document.getElementById(`badge-${bloque}`);
            if (badge) {
                badge.textContent = stats.por_bloque?.[bloque] || 0;
            }
        });
        
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

// Cargar editoriales
async function loadEditoriales(bloque = null) {
    showLoading();
    
    try {
        const url = bloque ? `/api/editoriales?bloque=${bloque}` : '/api/editoriales';
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error('Error cargando editoriales');
        }
        
        state.editoriales = await response.json();
        filterAndRender();
        
    } catch (error) {
        showError('Error cargando las editoriales: ' + error.message);
    }
}

// Filtrar y renderizar
function filterAndRender() {
    let filtered = state.editoriales;
    
    // Filtrar por búsqueda
    if (state.searchTerm) {
        filtered = filtered.filter(ed => 
            ed.nombre.toLowerCase().includes(state.searchTerm) ||
            (ed.grupo_editorial && ed.grupo_editorial.toLowerCase().includes(state.searchTerm))
        );
    }
    
    // Filtrar por estado
    if (state.filterEstado) {
        filtered = filtered.filter(ed => ed.estado === state.filterEstado);
    }
    
    state.filteredEditoriales = filtered;
    renderTable(filtered);
}

// Renderizar tabla
function renderTable(editoriales) {
    const tbody = document.getElementById('editoriales-tbody');
    const table = document.getElementById('editoriales-table');
    const loading = document.getElementById('loading');
    
    loading.style.display = 'none';
    
    if (editoriales.length === 0) {
        tbody.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 40px;">No hay editoriales para mostrar</td></tr>';
        table.style.display = 'table';
        return;
    }
    
    tbody.innerHTML = editoriales.map(ed => {
        const progreso = calcularProgreso(ed);
        const diasEnvio = calcularDiasDesdeEnvio(ed.fecha_envio, ed.fecha_respuesta);
        return `
        <tr data-estado="${ed.estado}">
            <td>${ed.orden || '-'}</td>
            <td style="text-align: center;">${generarBarraProgreso(progreso)}</td>
            <td><strong>${ed.nombre}</strong></td>
            <td>${ed.grupo_editorial || '-'}</td>
            <td>
                <span class="bloque-badge bloque-${ed.bloque}">${ed.bloque}</span>
            </td>
            <td>
                <span class="estado-${ed.estado}">${formatEstado(ed.estado)}</span>
            </td>
            <td style="text-align: center;">${diasEnvio}</td>
            <td>${ed.prioridad_global ? ed.prioridad_global.toFixed(2) : '-'}</td>
            <td>${ed.probabilidad_ajuste ? ed.probabilidad_ajuste.toFixed(1) : '-'}</td>
            <td>
                <button class="btn-action" onclick="viewDetalle(${ed.id})" title="Ver detalle">👁️</button>
                <button class="btn-action" onclick="editarEditorial(${ed.id})" title="Editar">✏️</button>
            </td>
        </tr>
        `;
    }).join('');
    
    table.style.display = 'table';
}

// Formatear estado
function formatEstado(estado) {
    const estados = {
        'pendiente': 'Pendiente',
        'en-proceso': 'En proceso',
        'en-evaluacion': 'En evaluación',
        'finalizado': 'Finalizado',
        'descartado': 'Descartado'
    };
    return estados[estado] || estado;
}

// Cambiar de tab
function switchTab(bloque) {
    state.currentBloque = bloque;
    
    // Actualizar UI de tabs
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.bloque === bloque) {
            btn.classList.add('active');
        }
    });
    
    // Cargar datos
    if (bloque === 'todos') {
        loadEditoriales();
    } else {
        loadEditoriales(bloque);
    }
}

// Ver detalle de editorial
function viewDetalle(id) {
    fetch(`/api/editoriales/${id}`)
        .then(res => res.json())
        .then(ed => {
            const modalBody = document.getElementById('modal-detalle-body');
            modalBody.innerHTML = `
                <h2>${ed.nombre}</h2>
                <p><strong>Grupo:</strong> ${ed.grupo_editorial || 'Independiente'}</p>
                <p><strong>Web:</strong> <a href="${ensureProtocol(ed.web)}" target="_blank">${ed.web}</a></p>
                
                <h3>Contacto</h3>
                <p><strong>Email:</strong> ${ed.email_principal || '-'}</p>
                <p><strong>URL general:</strong> ${ed.url_general ? `<a href="${ensureProtocol(ed.url_general)}" target="_blank">${ed.url_general}</a>` : '-'}</p>
                <p><strong>URL manuscritos:</strong> ${ed.url_manuscritos ? `<a href="${ensureProtocol(ed.url_manuscritos)}" target="_blank">${ed.url_manuscritos}</a>` : '-'}</p>
                <p><strong>Requiere formulario:</strong> ${ed.requiere_formulario ? '✓ Sí' : '✗ No'}</p>
                
                <h3>Seguimiento</h3>
                <p><strong>Bloque:</strong> ${ed.bloque}</p>
                <p><strong>Orden:</strong> ${ed.orden || '-'}</p>
                <p><strong>Estado:</strong> ${formatEstado(ed.estado)}</p>
                
                ${mostrarScoresIA(ed)}
                
                ${ed.notas ? `<h3>Notas</h3><p>${ed.notas}</p>` : ''}
                
                <div style="margin-top: 20px;">
                    <button onclick="closeModalDetalle()" class="btn-secondary">Cerrar</button>
                    <button onclick="editarEditorial(${ed.id}); closeModalDetalle();" class="btn-primary">✏️ Editar</button>
                    ${ed.analisis_ia ? `<button onclick="generarParrafoCarta(${ed.id})" class="btn-ia">✍️ Generar Párrafo</button>` : ''}
                    ${!ed.analisis_ia ? `<button onclick="analizarEditorial(${ed.id}).then(() => viewDetalle(${ed.id}))" class="btn-ia">🤖 Analizar con IA</button>` : ''}
                </div>
            `;
            document.getElementById('modal-detalle').style.display = 'block';
        })
        .catch(err => {
            showToast('Error cargando detalle: ' + err.message, 'error');
        });
}

// Editar editorial
async function editarEditorial(id) {
    try {
        // Cargar datos de la editorial
        const response = await fetch(`/api/editoriales/${id}`);
        const ed = await response.json();
        
        // Rellenar formulario
        document.getElementById('edit-id').value = ed.id;
        document.getElementById('edit-nombre').value = ed.nombre;
        document.getElementById('edit-grupo').value = ed.grupo_editorial || 'Independiente';
        document.getElementById('edit-bloque').value = ed.bloque || 'D';
        document.getElementById('edit-orden').value = ed.orden || '';
        document.getElementById('edit-estado').value = ed.estado || 'pendiente';
        document.getElementById('edit-fecha-confeccion').value = ed.fecha_confeccion || '';
        document.getElementById('edit-fecha-envio').value = ed.fecha_envio || '';
        document.getElementById('edit-fecha-respuesta').value = ed.fecha_respuesta || '';
        document.getElementById('edit-resultado').value = ed.resultado || '';
        document.getElementById('edit-notas').value = ed.notas || '';
        document.getElementById('edit-analisis-manual').value = ed.analisis_manual || '';
        document.getElementById('edit-feedback').value = ed.feedback_editorial || '';
        document.getElementById('edit-aprendizajes').value = ed.aprendizajes || '';
        
        // Mostrar modal
        document.getElementById('modal-editar').style.display = 'block';
        
    } catch (error) {
        showToast('Error cargando editorial: ' + error.message, 'error');
    }
}

// Guardar edición
async function guardarEdicion() {
    const id = document.getElementById('edit-id').value;
    
    // Recoger datos del formulario
    const data = {
        bloque: document.getElementById('edit-bloque').value,
        orden: parseInt(document.getElementById('edit-orden').value) || null,
        estado: document.getElementById('edit-estado').value,
        fecha_confeccion: document.getElementById('edit-fecha-confeccion').value || null,
        fecha_envio: document.getElementById('edit-fecha-envio').value || null,
        fecha_respuesta: document.getElementById('edit-fecha-respuesta').value || null,
        resultado: document.getElementById('edit-resultado').value || null,
        notas: document.getElementById('edit-notas').value || null,
        analisis_manual: document.getElementById('edit-analisis-manual').value || null,
        feedback_editorial: document.getElementById('edit-feedback').value || null,
        aprendizajes: document.getElementById('edit-aprendizajes').value || null
    };
    
    try {
        const response = await fetch(`/api/editoriales/${id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast('✓ Cambios guardados correctamente', 'success');
            closeModalEditar();
            
            // Recargar datos
            if (state.currentBloque === 'todos') {
                loadEditoriales();
            } else {
                loadEditoriales(state.currentBloque);
            }
            loadStats();
        } else {
            showToast('Error: ' + result.error, 'error');
        }
        
    } catch (error) {
        showToast('Error guardando cambios: ' + error.message, 'error');
    }
}

// Normalizar orden de bloque
async function normalizarOrden(bloque) {
    if (!confirm(`¿Normalizar el orden del bloque ${bloque}? (100, 200, 300...)`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/bloques/${bloque}/normalizar`, {
            method: 'POST'
        });
        
        const result = await response.json();
        
        if (result.success) {
            alert(result.message);
            loadEditoriales(bloque);
        } else {
            alert('Error normalizando: ' + result.error);
        }
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

// Utilidades UI
function showLoading() {
    document.getElementById('loading').style.display = 'block';
    document.getElementById('editoriales-table').style.display = 'none';
    document.getElementById('error').style.display = 'none';
}

function showError(message) {
    document.getElementById('loading').style.display = 'none';
    document.getElementById('editoriales-table').style.display = 'none';
    const errorDiv = document.getElementById('error');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
}

function closeModalDetalle() {
    document.getElementById('modal-detalle').style.display = 'none';
}

function closeModalEditar() {
    document.getElementById('modal-editar').style.display = 'none';
}

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type} show`;
    
    setTimeout(() => {
        toast.className = 'toast';
    }, 3000);
}

// ============================================================================
// FUNCIONES DE ANÁLISIS IA
// ============================================================================

async function verificarIADisponible() {
    const apiKey = getApiKey();
    const btnAnalizar = document.getElementById('btn-analizar-todas');
    
    if (!apiKey) {
        btnAnalizar.disabled = true;
        btnAnalizar.title = 'Configura tu API key primero (botón ⚙️)';
        console.warn('API key no configurada');
        return;
    }
    
    try {
        const response = await fetch('/api/ia/disponible', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const data = await response.json();
        
        if (!data.disponible) {
            btnAnalizar.disabled = true;
            btnAnalizar.title = data.mensaje;
        } else {
            btnAnalizar.disabled = false;
            btnAnalizar.title = 'Analizar todas las editoriales con IA';
        }
    } catch (error) {
        console.error('Error verificando IA:', error);
        btnAnalizar.disabled = true;
    }
}

async function analizarEditorial(id) {
    const apiKey = getApiKey();
    
    if (!apiKey) {
        showToast('⚠️ Configura tu API key primero (botón ⚙️)', 'error');
        return null;
    }
    
    const manuscrito = getManuscritoData();
    
    if (!manuscrito.descripcion) {
        showToast('⚠️ Configura tu manuscrito primero (botón ⚙️)', 'error');
        abrirModalConfig();
        return null;
    }
    
    try {
        const response = await fetch(`/api/analizar/${id}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                api_key: apiKey,
                manuscrito: manuscrito
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`✓ ${result.message}`, 'success');
            return result.scores;
        } else {
            showToast(`Error: ${result.error}`, 'error');
            return null;
        }
    } catch (error) {
        showToast('Error analizando: ' + error.message, 'error');
        return null;
    }
}

async function analizarTodas() {
    const apiKey = getApiKey();
    
    if (!apiKey) {
        showToast('⚠️ Configura tu API key primero (botón ⚙️)', 'error');
        abrirModalConfig();
        return;
    }
    
    const manuscrito = getManuscritoData();
    
    if (!manuscrito.descripcion) {
        showToast('⚠️ Configura tu manuscrito primero (botón ⚙️)', 'error');
        abrirModalConfig();
        return;
    }
    
    const confirmar = confirm(
        '¿Analizar todas las editoriales sin análisis IA?\n\n' +
        'Esto puede tardar varios minutos y consumirá créditos de tu API de Anthropic.\n\n' +
        'Coste estimado: $2-5 aproximadamente.'
    );
    
    if (!confirmar) return;
    
    // Mostrar modal de progreso
    document.getElementById('modal-analisis-progreso').style.display = 'block';
    document.getElementById('progreso-texto').textContent = 'Conectando con API...';
    document.getElementById('progreso-contador').textContent = '0 / ?';
    document.getElementById('progress-fill').style.width = '0%';
    document.getElementById('progreso-log').innerHTML = '';
    document.getElementById('btn-cerrar-progreso').style.display = 'none';
    
    try {
        // Iniciar análisis batch con POST
        const response = await fetch('/api/analizar-todas', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: apiKey,
                manuscrito: manuscrito
            })
        });
        
        // Leer respuesta como stream
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let total = 0;
        let current = 0;
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            // Decodificar chunk
            const chunk = decoder.decode(value);
            const lines = chunk.split('\n');
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        
                        switch(data.type) {
                            case 'start':
                                total = data.total;
                                document.getElementById('progreso-contador').textContent = `0 / ${total}`;
                                document.getElementById('progreso-texto').textContent = 
                                    `Analizando ${total} editoriales...`;
                                break;
                            
                            case 'progress':
                                current = data.current;
                                const percent = (current / data.total) * 100;
                                document.getElementById('progress-fill').style.width = percent + '%';
                                document.getElementById('progreso-contador').textContent = 
                                    `${current} / ${data.total}`;
                                document.getElementById('progreso-texto').textContent = 
                                    `Analizando: ${data.nombre}...`;
                                break;
                            
                            case 'success':
                                agregarLogItem(`✓ ${data.nombre} - Prioridad: ${data.prioridad}`, 'success');
                                break;
                            
                            case 'error':
                                agregarLogItem(`✗ Error: ${data.nombre}`, 'error');
                                break;
                            
                            case 'complete':
                                document.getElementById('progress-fill').style.width = '100%';
                                document.getElementById('progreso-texto').textContent = 
                                    '✓ ' + data.message;
                                document.getElementById('btn-cerrar-progreso').style.display = 'block';
                                
                                // Recargar datos
                                setTimeout(() => {
                                    loadEditoriales();
                                    loadStats();
                                }, 1000);
                                break;
                        }
                    } catch (e) {
                        // Ignorar errores de parsing
                    }
                }
            }
        }
        
    } catch (error) {
        showToast('Error iniciando análisis: ' + error.message, 'error');
        document.getElementById('progreso-texto').textContent = '✗ Error en la conexión';
        document.getElementById('btn-cerrar-progreso').style.display = 'block';
    }
}

function agregarLogItem(texto, tipo = '') {
    const log = document.getElementById('progreso-log');
    const item = document.createElement('div');
    item.className = `progreso-log-item ${tipo}`;
    item.textContent = texto;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
}

function cerrarModalProgreso() {
    document.getElementById('modal-analisis-progreso').style.display = 'none';
}

function mostrarScoresIA(editorial) {
    if (!editorial.analisis_ia) return '';
    
    const scores = {
        'Tamaño': editorial.tamaño || 0,
        'Género': editorial.genero_ajuste || 0,
        'Prestigio': editorial.prestigio || 0,
        'Distribución': editorial.distribucion || 0,
        'Promoción': editorial.promocion || 0,
        'Probabilidad': editorial.probabilidad_ajuste || 0
    };
    
    let html = '<div class="analisis-ia-section">';
    html += '<h3>🤖 Análisis IA</h3>';
    html += '<div class="scores-grid">';
    
    for (const [label, value] of Object.entries(scores)) {
        const percent = (value / 10) * 100;
        html += `
            <div class="score-item">
                <div class="score-label">${label}</div>
                <div class="score-value">${value}/10</div>
                <div class="score-bar">
                    <div class="score-bar-fill" style="width: ${percent}%"></div>
                </div>
            </div>
        `;
    }
    
    html += `
        <div class="score-global">
            <div class="score-label">Prioridad Global</div>
            <div class="score-value">${editorial.prioridad_global?.toFixed(2) || 0}/10</div>
        </div>
    `;
    
    html += '</div>';
    html += `<p class="analisis-texto">${editorial.analisis_ia}</p>`;
    html += `<button onclick="analizarEditorial(${editorial.id})" class="btn-reanalizar">🔄 Re-analizar</button>`;
    html += '</div>';
    
    return html;
}

// ============================================================================
// FUNCIONES DE CONFIGURACIÓN
// ============================================================================

function abrirModalConfig() {
    // Cargar API key actual si existe
    const apiKey = localStorage.getItem('anthropic_api_key');
    const input = document.getElementById('input-api-key');
    
    if (apiKey) {
        input.value = apiKey;
        mostrarEstadoApiKey('✓ API key configurada', 'success');
    } else {
        input.value = '';
        mostrarEstadoApiKey('⚠️ No hay API key configurada', 'info');
    }
    
    document.getElementById('modal-config').style.display = 'block';
}

function closeModalConfig() {
    document.getElementById('modal-config').style.display = 'none';
}

function toggleApiKeyVisibility() {
    const input = document.getElementById('input-api-key');
    const btn = document.getElementById('btn-toggle-key');
    
    if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = '🙈 Ocultar';
    } else {
        input.type = 'password';
        btn.textContent = '👁️ Mostrar';
    }
}

function mostrarEstadoApiKey(mensaje, tipo) {
    const statusDiv = document.getElementById('api-key-status');
    statusDiv.textContent = mensaje;
    statusDiv.className = `api-key-status ${tipo}`;
}

async function testApiKey() {
    const apiKey = document.getElementById('input-api-key').value.trim();
    
    if (!apiKey) {
        mostrarEstadoApiKey('❌ Por favor, introduce una API key', 'error');
        return;
    }
    
    if (!apiKey.startsWith('sk-ant-')) {
        mostrarEstadoApiKey('❌ La API key debe empezar con "sk-ant-"', 'error');
        return;
    }
    
    mostrarEstadoApiKey('🔄 Probando conexión con Anthropic...', 'info');
    
    try {
        // Probar la API key haciendo una llamada real
        const response = await fetch('/api/test-api-key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ api_key: apiKey })
        });
        
        const result = await response.json();
        
        if (result.success) {
            mostrarEstadoApiKey('✅ API key válida - Conexión exitosa', 'success');
        } else {
            mostrarEstadoApiKey(`❌ Error: ${result.error}`, 'error');
        }
    } catch (error) {
        mostrarEstadoApiKey('❌ Error probando conexión: ' + error.message, 'error');
    }
}

function guardarApiKey() {
    const apiKey = document.getElementById('input-api-key').value.trim();
    
    if (!apiKey) {
        mostrarEstadoApiKey('❌ Por favor, introduce una API key', 'error');
        return;
    }
    
    if (!apiKey.startsWith('sk-ant-')) {
        mostrarEstadoApiKey('❌ La API key debe empezar con "sk-ant-"', 'error');
        return;
    }
    
    // Guardar en localStorage
    localStorage.setItem('anthropic_api_key', apiKey);
    
    mostrarEstadoApiKey('✅ API key guardada correctamente', 'success');
    showToast('✓ API key guardada', 'success');
    
    // Actualizar estado de análisis IA
    verificarIADisponible();
}

function eliminarApiKey() {
    const confirmar = confirm('¿Eliminar la API key guardada?\n\nTendrás que configurarla de nuevo para usar el análisis IA.');
    
    if (!confirmar) return;
    
    localStorage.removeItem('anthropic_api_key');
    document.getElementById('input-api-key').value = '';
    
    mostrarEstadoApiKey('ℹ️ API key eliminada', 'info');
    showToast('API key eliminada', 'success');
    
    // Actualizar estado
    verificarIADisponible();
}

// Obtener API key para las llamadas
function getApiKey() {
    return localStorage.getItem('anthropic_api_key');
}

// Función auxiliar para asegurar que las URLs tienen protocolo
function ensureProtocol(url) {
    if (!url) return '';
    url = url.trim();
    if (!url.startsWith('http://') && !url.startsWith('https://')) {
        return 'https://' + url;
    }
    return url;
}

// ============================================================================
// FUNCIONES DE GESTIÓN DE MANUSCRITO
// ============================================================================

// Estado de archivos
let manuscritoFiles = {
    sinopsis: null,
    muestra: null
};

// Cargar configuración de manuscrito al abrir modal
function cargarConfigManuscrito() {
    // Cargar descripción
    const desc = localStorage.getItem('manuscrito_descripcion');
    if (desc) {
        document.getElementById('input-manuscrito-desc').value = desc;
    }
    
    // Cargar info de archivos (sin el contenido completo)
    const sinopsisInfo = localStorage.getItem('manuscrito_sinopsis_info');
    const muestraInfo = localStorage.getItem('manuscrito_muestra_info');
    
    if (sinopsisInfo) {
        const info = JSON.parse(sinopsisInfo);
        mostrarArchivoPreview('sinopsis', info.name, info.size);
    }
    
    if (muestraInfo) {
        const info = JSON.parse(muestraInfo);
        mostrarArchivoPreview('muestra', info.name, info.size);
    }
}

// Manejar cambio de archivo sinopsis
document.getElementById('input-sinopsis').addEventListener('change', function(e) {
    manejarArchivoTXT('sinopsis', e.target.files[0]);
});

// Manejar cambio de archivo muestra
document.getElementById('input-muestra').addEventListener('change', function(e) {
    manejarArchivoTXT('muestra', e.target.files[0]);
});

async function manejarArchivoTXT(tipo, file) {
    if (!file) return;
    
    // Solo aceptar archivos de texto
    if (!file.name.endsWith('.txt')) {
        mostrarEstadoManuscrito('⚠️ Por favor, sube archivos .TXT (puedes copiar tu sinopsis/muestra a un archivo de texto)', 'error');
        document.getElementById(`input-${tipo}`).value = '';
        return;
    }
    
    // Validar tamaño (máx 1MB para texto)
    if (file.size > 1024 * 1024) {
        alert('El archivo es demasiado grande. Máximo 1MB.');
        return;
    }
    
    mostrarEstadoManuscrito('📄 Leyendo archivo...', 'info');
    
    try {
        const contenido = await new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = reject;
            reader.readAsText(file);
        });
        
        manuscritoFiles[tipo] = {
            name: file.name,
            size: file.size,
            type: 'text/plain',
            content: contenido
        };
        
        mostrarArchivoPreview(tipo, file.name, file.size);
        mostrarEstadoManuscrito(`✓ ${file.name} cargado`, 'success');
        
    } catch (error) {
        console.error('Error leyendo archivo:', error);
        mostrarEstadoManuscrito('✗ Error leyendo archivo', 'error');
    }
}

function manejarArchivoSubido(tipo, file) {
    if (!file) return;
    
    // Validar tamaño (máx 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('El archivo es demasiado grande. Máximo 5MB.');
        return;
    }
    
    // Leer archivo
    const reader = new FileReader();
    reader.onload = function(e) {
        manuscritoFiles[tipo] = {
            name: file.name,
            size: file.size,
            type: file.type,
            content: e.target.result // Base64
        };
        
        mostrarArchivoPreview(tipo, file.name, file.size);
        mostrarEstadoManuscrito(`✓ ${file.name} cargado`, 'success');
    };
    
    reader.onerror = function() {
        mostrarEstadoManuscrito('✗ Error leyendo archivo', 'error');
    };
    
    reader.readAsDataURL(file);
}

function mostrarArchivoPreview(tipo, nombre, size) {
    const preview = document.getElementById(`${tipo}-preview`);
    const sizeKB = (size / 1024).toFixed(1);
    
    preview.innerHTML = `
        <span class="archivo-nombre">✓ ${nombre}</span>
        <span class="archivo-size">(${sizeKB} KB)</span>
        <button class="btn-remove-file" onclick="eliminarArchivo('${tipo}')">✕</button>
    `;
    preview.classList.add('active');
}

function eliminarArchivo(tipo) {
    manuscritoFiles[tipo] = null;
    document.getElementById(`${tipo}-preview`).classList.remove('active');
    document.getElementById(`input-${tipo}`).value = '';
    
    // Eliminar de localStorage
    localStorage.removeItem(`manuscrito_${tipo}_info`);
    localStorage.removeItem(`manuscrito_${tipo}_content`);
    
    mostrarEstadoManuscrito('Archivo eliminado', 'info');
}

function mostrarEstadoManuscrito(mensaje, tipo) {
    const statusDiv = document.getElementById('manuscrito-status');
    statusDiv.textContent = mensaje;
    statusDiv.className = `api-key-status ${tipo}`;
    
    setTimeout(() => {
        statusDiv.className = 'api-key-status';
    }, 3000);
}

function guardarManuscrito() {
    const descripcion = document.getElementById('input-manuscrito-desc').value.trim();
    
    if (!descripcion) {
        mostrarEstadoManuscrito('⚠️ Escribe al menos una descripción de tu manuscrito', 'error');
        return;
    }
    
    // Guardar descripción
    localStorage.setItem('manuscrito_descripcion', descripcion);
    
    // Guardar archivos si existen (con límite de caracteres)
    if (manuscritoFiles.sinopsis) {
        // Limitar sinopsis a 2500 caracteres
        const contenidoLimitado = manuscritoFiles.sinopsis.content.substring(0, 2500);
        
        localStorage.setItem('manuscrito_sinopsis_info', JSON.stringify({
            name: manuscritoFiles.sinopsis.name,
            size: manuscritoFiles.sinopsis.size,
            type: 'text/plain'
        }));
        localStorage.setItem('manuscrito_sinopsis_content', contenidoLimitado);
    }
    
    if (manuscritoFiles.muestra) {
        // Limitar muestra a 3000 caracteres (primeras 5-6 páginas)
        const contenidoLimitado = manuscritoFiles.muestra.content.substring(0, 3000);
        
        localStorage.setItem('manuscrito_muestra_info', JSON.stringify({
            name: manuscritoFiles.muestra.name,
            size: manuscritoFiles.muestra.size,
            type: 'text/plain'
        }));
        localStorage.setItem('manuscrito_muestra_content', contenidoLimitado);
    }
    
    mostrarEstadoManuscrito('✓ Manuscrito guardado correctamente', 'success');
    showToast('✓ Configuración de manuscrito guardada', 'success');
}

function limpiarManuscrito() {
    if (!confirm('¿Eliminar toda la configuración de manuscrito?')) {
        return;
    }
    
    // Limpiar campos
    document.getElementById('input-manuscrito-desc').value = '';
    eliminarArchivo('sinopsis');
    eliminarArchivo('muestra');
    
    // Limpiar localStorage
    localStorage.removeItem('manuscrito_descripcion');
    
    mostrarEstadoManuscrito('Configuración eliminada', 'info');
    showToast('Configuración de manuscrito eliminada', 'success');
}

// Obtener datos del manuscrito para enviar al servidor
function getManuscritoData() {
    const desc = localStorage.getItem('manuscrito_descripcion');
    const sinopsisContent = localStorage.getItem('manuscrito_sinopsis_content');
    const muestraContent = localStorage.getItem('manuscrito_muestra_content');
    
    return {
        descripcion: desc || 'Novela literaria contemporánea en español',
        sinopsis: sinopsisContent || null,
        muestra: muestraContent || null
    };
}

// Actualizar función de abrir modal config para cargar manuscrito
const abrirModalConfigOriginal = abrirModalConfig;
abrirModalConfig = function() {
    abrirModalConfigOriginal();
    cargarConfigManuscrito();
};

// ============================================================================
// EXTRACCIÓN DE TEXTO DE PDFs
// ============================================================================

// Cargar librería PDF.js para extraer texto
const pdfjsLib = window['pdfjs-dist/build/pdf'];
if (pdfjsLib) {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
}

async function extraerTextoDePDF(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        
        reader.onload = async function(e) {
            try {
                const typedarray = new Uint8Array(e.target.result);
                const pdf = await pdfjsLib.getDocument(typedarray).promise;
                
                let textoCompleto = '';
                
                // Extraer texto de cada página
                for (let i = 1; i <= pdf.numPages; i++) {
                    const page = await pdf.getPage(i);
                    const textContent = await page.getTextContent();
                    const pageText = textContent.items.map(item => item.str).join(' ');
                    textoCompleto += pageText + '\n\n';
                }
                
                resolve(textoCompleto);
            } catch (error) {
                console.error('Error extrayendo texto de PDF:', error);
                reject(error);
            }
        };
        
        reader.onerror = function() {
            reject(new Error('Error leyendo archivo'));
        };
        
        reader.readAsArrayBuffer(file);
    });
}

// Actualizar función de manejo de archivos para extraer texto
async function manejarArchivoSubidoV2(tipo, file) {
    if (!file) return;
    
    // Validar tamaño (máx 5MB)
    if (file.size > 5 * 1024 * 1024) {
        alert('El archivo es demasiado grande. Máximo 5MB.');
        return;
    }
    
    mostrarEstadoManuscrito('📄 Procesando archivo...', 'info');
    
    try {
        let contenido = '';
        
        // Si es PDF, extraer texto
        if (file.type === 'application/pdf') {
            contenido = await extraerTextoDePDF(file);
        } 
        // Si es texto plano
        else if (file.type === 'text/plain') {
            contenido = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = (e) => resolve(e.target.result);
                reader.onerror = reject;
                reader.readAsText(file);
            });
        }
        // Si es Word (.doc, .docx), no podemos procesarlo en frontend
        else {
            mostrarEstadoManuscrito('⚠️ Solo PDF y TXT soportados por ahora', 'error');
            return;
        }
        
        manuscritoFiles[tipo] = {
            name: file.name,
            size: file.size,
            type: 'text/plain', // Guardamos como texto
            content: contenido  // Texto extraído, no base64
        };
        
        mostrarArchivoPreview(tipo, file.name, file.size);
        mostrarEstadoManuscrito(`✓ ${file.name} procesado (texto extraído)`, 'success');
        
    } catch (error) {
        console.error('Error procesando archivo:', error);
        mostrarEstadoManuscrito('✗ Error procesando archivo', 'error');
    }
}

// ============================================================================
// ASIGNACIÓN AUTOMÁTICA DE BLOQUES
// ============================================================================

async function asignarBloquesAutomaticamente() {
    // Verificar que hay editoriales con análisis IA
    const editoriales = await fetch('/api/editoriales').then(r => r.json());
    const conAnalisis = editoriales.filter(e => e.analisis_ia);
    
    if (conAnalisis.length === 0) {
        showToast('⚠️ Primero debes analizar editoriales con IA', 'error');
        return;
    }
    
    const confirmar = confirm(
        `¿Asignar bloques automáticamente a ${conAnalisis.length} editoriales?\n\n` +
        'Los bloques se asignarán según las puntuaciones IA:\n' +
        '• Bloque A: Prioridad máxima\n' +
        '• Bloque B: Buenas opciones\n' +
        '• Bloque C: Opciones de backup\n' +
        '• Bloque D: Descartadas'
    );
    
    if (!confirmar) return;
    
    try {
        showToast('📊 Asignando bloques...', 'info');
        
        const response = await fetch('/api/asignar-bloques', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`✓ ${result.message}`, 'success');
            
            // Mostrar estadísticas
            mostrarEstadisticasBloques(result.estadisticas);
            
            // Recargar datos
            loadEditoriales();
            loadStats();
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Error asignando bloques: ' + error.message, 'error');
    }
}

function mostrarEstadisticasBloques(stats) {
    const modal = document.getElementById('modal-bloques-stats');
    const content = document.getElementById('bloques-stats-content');
    
    const explicaciones = {
        'A': 'Prioridad máxima: Excelente ajuste de género, alta prioridad, buena visibilidad',
        'B': 'Buenas opciones: Buen ajuste, prioridad media-alta',
        'C': 'Opciones de backup: Ajuste aceptable, menor prioridad',
        'D': 'Descartadas: Bajo ajuste o no adecuadas para el manuscrito'
    };
    
    let html = '';
    
    for (const bloque of ['A', 'B', 'C', 'D']) {
        const data = stats[bloque];
        const prioridad = data.prioridad_media || 0;
        
        html += `
            <div class="bloque-stat bloque-${bloque.toLowerCase()}">
                <div class="bloque-stat-header">
                    <div class="bloque-stat-title">Bloque ${bloque}</div>
                    <div class="bloque-stat-count">${data.count}</div>
                </div>
                <div class="bloque-stat-info">
                    Prioridad media: ${prioridad.toFixed(2)}
                </div>
                <div class="bloque-stat-desc">
                    ${explicaciones[bloque]}
                </div>
            </div>
        `;
    }
    
    content.innerHTML = html;
    modal.style.display = 'block';
}

function cerrarModalBloques() {
    document.getElementById('modal-bloques-stats').style.display = 'none';
}

// Cerrar modal al hacer click fuera
window.addEventListener('click', function(event) {
    const modal = document.getElementById('modal-bloques-stats');
    if (event.target === modal) {
        cerrarModalBloques();
    }
});

// ============================================================================
// ORDENAR POR PRIORIDAD IA
// ============================================================================

async function ordenarPorPrioridad() {
    const confirmar = confirm(
        '¿Ordenar editoriales por Prioridad IA?\n\n' +
        'Esto actualizará el campo "orden" poniendo primero\n' +
        'las editoriales con mayor prioridad global.\n\n' +
        'Luego podrás ajustar manualmente si lo deseas.'
    );
    
    if (!confirmar) return;
    
    try {
        showToast('🎯 Ordenando por prioridad...', 'info');
        
        const response = await fetch('/api/ordenar-por-prioridad', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`✓ ${result.message}`, 'success');
            
            // Recargar datos
            loadEditoriales();
            loadStats();
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Error ordenando: ' + error.message, 'error');
    }
}

// Conectar botón
document.getElementById('btn-ordenar-prioridad').addEventListener('click', ordenarPorPrioridad);

// ============================================================================
// ORDENAR POR PROBABILIDAD
// ============================================================================

async function ordenarPorProbabilidad() {
    const confirmar = confirm(
        '¿Ordenar editoriales por Probabilidad de Aceptación?\n\n' +
        'Esto actualizará el campo "orden" poniendo primero\n' +
        'las editoriales con mayor probabilidad de aceptación.\n\n' +
        'Estrategia: Empezar por donde tienes más opciones.'
    );
    
    if (!confirmar) return;
    
    try {
        showToast('🎲 Ordenando por probabilidad...', 'info');
        
        const response = await fetch('/api/ordenar-por-probabilidad', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showToast(`✓ ${result.message}`, 'success');
            
            // Recargar datos
            loadEditoriales();
            loadStats();
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Error ordenando: ' + error.message, 'error');
    }
}

// Conectar botón
document.getElementById('btn-ordenar-probabilidad').addEventListener('click', ordenarPorProbabilidad);

// ============================================================================
// GENERACIÓN DE PÁRRAFOS PARA CARTAS
// ============================================================================

let parrafoGenerado = '';

async function generarParrafoCarta(editorialId) {
    const apiKey = getApiKey();
    
    if (!apiKey) {
        showToast('⚠️ Configura tu API key primero (botón ⚙️)', 'error');
        return;
    }
    
    const manuscrito = getManuscritoData();
    
    if (!manuscrito.descripcion) {
        showToast('⚠️ Configura tu manuscrito primero (botón ⚙️)', 'error');
        abrirModalConfig();
        return;
    }
    
    // Verificar si ya existe un párrafo guardado
    try {
        const editorialResponse = await fetch(`/api/editoriales/${editorialId}`);
        const editorial = await editorialResponse.json();
        
        if (editorial.analisis_manual && editorial.analisis_manual.trim()) {
            const confirmar = confirm(
                '⚠️ Ya existe un párrafo guardado para esta editorial.\n\n' +
                'Si generas uno nuevo y lo guardas, se sobreescribirá el anterior.\n\n' +
                '¿Continuar y generar un nuevo párrafo?'
            );
            
            if (!confirmar) {
                return;
            }
        }
    } catch (error) {
        console.error('Error verificando párrafo existente:', error);
    }
    
    try {
        showToast('✍️ Generando párrafo personalizado...', 'info');
        
        const response = await fetch(`/api/generar-parrafo/${editorialId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: apiKey,
                manuscrito: manuscrito
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            parrafoGenerado = result.parrafo;
            document.getElementById('parrafo-editorial-id').value = editorialId;
            document.getElementById('parrafo-editorial-nombre').textContent = `Para: ${result.editorial}`;
            document.getElementById('parrafo-content').textContent = result.parrafo;
            document.getElementById('modal-parrafo').style.display = 'block';
            showToast('✓ Párrafo generado', 'success');
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Error generando párrafo: ' + error.message, 'error');
    }
}

function copiarParrafo() {
    if (!parrafoGenerado) return;
    
    navigator.clipboard.writeText(parrafoGenerado).then(() => {
        showToast('✓ Párrafo copiado al portapapeles', 'success');
    }).catch(err => {
        showToast('Error copiando: ' + err.message, 'error');
    });
}

async function guardarParrafo() {
    const editorialId = document.getElementById('parrafo-editorial-id').value;
    
    if (!parrafoGenerado || !editorialId) {
        showToast('Error: No hay párrafo para guardar', 'error');
        return;
    }
    
    try {
        const response = await fetch(`/api/editoriales/${editorialId}/guardar-parrafo`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                parrafo: parrafoGenerado
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 1. Cerrar modal párrafo
            cerrarModalParrafo();
            
            // 2. Cerrar modal detalle si está abierto
            closeModalDetalle();
            
            // 3. Abrir modal edición
            await editarEditorial(editorialId);
            
            // 4. Confirmación
            showToast('✓ Párrafo guardado en "Párrafo personalizado para carta"', 'success');
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Error guardando párrafo: ' + error.message, 'error');
    }
}

function cerrarModalParrafo() {
    document.getElementById('modal-parrafo').style.display = 'none';
    document.getElementById('instrucciones-refinamiento').value = ''; // Limpiar instrucciones
}

// Cerrar modal al hacer click fuera
window.addEventListener('click', function(event) {
    const modal = document.getElementById('modal-parrafo');
    if (event.target === modal) {
        cerrarModalParrafo();
    }
});

// ============================================================================
// INDICADOR DE PROGRESO
// ============================================================================

function calcularProgreso(editorial) {
    /**
     * Calcula el progreso de completitud de una editorial
     * 4 criterios (25% cada uno):
     * 1. Análisis IA
     * 2. Notas
     * 3. Párrafo (analisis_manual)
     * 4. Enviado (fecha_envio)
     */
    let puntos = 0;
    
    if (editorial.analisis_ia && editorial.analisis_ia.trim()) puntos += 1;
    if (editorial.notas && editorial.notas.trim()) puntos += 1;
    if (editorial.analisis_manual && editorial.analisis_manual.trim()) puntos += 1;
    if (editorial.fecha_envio) puntos += 1;
    
    return (puntos / 4) * 100;
}

function generarBarraProgreso(progreso) {
    /**
     * Genera el HTML de la barra de progreso vertical
     */
    let levelClass = 'level-0';
    
    if (progreso >= 100) levelClass = 'level-100';
    else if (progreso >= 75) levelClass = 'level-75';
    else if (progreso >= 50) levelClass = 'level-50';
    else if (progreso >= 25) levelClass = 'level-25';
    
    return `
        <div class="progress-bar-mini" title="Progreso: ${progreso}% (Análisis/Notas/Párrafo/Envío)">
            <div class="progress-fill-mini ${levelClass}"></div>
        </div>
    `;
}

// ============================================================================
// REFINAMIENTO DE PÁRRAFOS
// ============================================================================

async function refinarParrafo() {
    const editorialId = document.getElementById('parrafo-editorial-id').value;
    const instrucciones = document.getElementById('instrucciones-refinamiento').value.trim();
    
    if (!instrucciones) {
        showToast('⚠️ Por favor escribe instrucciones de refinamiento', 'error');
        return;
    }
    
    if (!parrafoGenerado || !editorialId) {
        showToast('⚠️ Error: No hay párrafo para refinar', 'error');
        return;
    }
    
    const apiKey = getApiKey();
    if (!apiKey) {
        showToast('⚠️ API key no configurada', 'error');
        return;
    }
    
    const manuscrito = getManuscritoData();
    
    try {
        showToast('🔄 Refinando párrafo...', 'info');
        
        const response = await fetch(`/api/refinar-parrafo/${editorialId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                api_key: apiKey,
                manuscrito: manuscrito,
                parrafo_anterior: parrafoGenerado,
                instrucciones: instrucciones
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            // Actualizar con el párrafo refinado
            parrafoGenerado = result.parrafo;
            document.getElementById('parrafo-content').textContent = result.parrafo;
            
            // Limpiar instrucciones para próxima iteración
            document.getElementById('instrucciones-refinamiento').value = '';
            
            showToast('✓ Párrafo refinado', 'success');
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
    } catch (error) {
        showToast('Error refinando: ' + error.message, 'error');
    }
}

// ============================================================================
// CÁLCULO DE DÍAS DESDE ENVÍO
// ============================================================================

function calcularDiasDesdeEnvio(fechaEnvio, fechaRespuesta) {
    /**
     * Calcula días transcurridos desde la fecha de envío.
     * Si existe fecha de respuesta (finalizado), muestra la diferencia fija
     * entre ambas fechas en rojo. De lo contrario, cuenta desde hoy en verde.
     */
    if (!fechaEnvio) return '-';

    const envio = new Date(fechaEnvio);

    if (fechaRespuesta) {
        // Proceso finalizado: diferencia fija entre respuesta y envío
        const respuesta = new Date(fechaRespuesta);
        const diffDias = Math.floor((respuesta - envio) / (1000 * 60 * 60 * 24));
        if (diffDias < 0) return '-';
        const texto = diffDias === 1 ? '1 día' : `${diffDias} días`;
        return `<span style="color: #e74c3c;">${texto}</span>`;
    }

    // Proceso en curso: días transcurridos hasta hoy
    const diffDias = Math.floor((new Date() - envio) / (1000 * 60 * 60 * 24));
    if (diffDias < 0) return '-';
    if (diffDias === 0) return '<span style="color: #27ae60;">Hoy</span>';
    if (diffDias === 1) return '<span style="color: #27ae60;">1 día</span>';
    if (diffDias < 30) return `<span style="color: #27ae60;">${diffDias} días</span>`;
    if (diffDias < 60) return `<span style="color: #f39c12;">${diffDias} días</span>`;
    if (diffDias < 90) return `<span style="color: #e67e22;">${diffDias} días</span>`;
    return `<span style="color: #e74c3c;">${diffDias} días</span>`; // 90+ días
}

// ============================================================================
// NAVEGACIÓN: VER DETALLE DESDE EDICIÓN
// ============================================================================

function verDetalleDesdeEdicion() {
    /**
     * Permite ver el detalle de una editorial desde el modal de edición
     * sin tener que cerrar y buscar de nuevo
     */
    const editorialId = document.getElementById('edit-id').value;
    
    if (!editorialId) {
        showToast('Error: No se puede determinar la editorial', 'error');
        return;
    }
    
    // Cerrar modal de edición
    closeModalEditar();
    
    // Abrir modal de detalle
    viewDetalle(editorialId);
}

// ============================================================================
// CREAR NUEVA EDITORIAL
// ============================================================================

function openModalNuevaEditorial() {
    /**
     * Abre el modal para crear una nueva editorial
     */
    document.getElementById('modal-nueva-editorial').style.display = 'block';
    // Limpiar formulario
    document.getElementById('form-nueva-editorial').reset();
    document.getElementById('nueva-analizar').checked = true; // Por defecto, analizar
}

function closeModalNuevaEditorial() {
    /**
     * Cierra el modal de nueva editorial
     */
    document.getElementById('modal-nueva-editorial').style.display = 'none';
}

async function guardarNuevaEditorial(event) {
    /**
     * Guarda una nueva editorial y opcionalmente la analiza con IA
     */
    event.preventDefault();
    
    // Recoger datos del formulario
    const data = {
        nombre: document.getElementById('nueva-nombre').value.trim(),
        web: document.getElementById('nueva-web').value.trim(),
        grupo_editorial: document.getElementById('nueva-grupo').value.trim() || 'Independiente',
        email_principal: document.getElementById('nueva-email').value.trim(),
        analizar: document.getElementById('nueva-analizar').checked
    };
    
    // Validar campos obligatorios
    if (!data.nombre) {
        showToast('El nombre es obligatorio', 'error');
        return;
    }
    
    if (!data.web) {
        showToast('La web es obligatoria', 'error');
        return;
    }
    
    // Si se va a analizar, necesitamos API key y manuscrito
    if (data.analizar) {
        const apiKey = localStorage.getItem('anthropic_api_key');
        const manuscritoConfig = getManuscritoData();
        
        if (!apiKey) {
            showToast('Para analizar con IA necesitas configurar la API key en Configuración', 'error');
            return;
        }
        
        if (!manuscritoConfig.descripcion) {
            showToast('Para analizar con IA necesitas configurar la descripción del manuscrito en Configuración', 'error');
            return;
        }
        
        data.api_key = apiKey;
        data.manuscrito = manuscritoConfig;
    }
    
    // Mostrar loading
    showToast('Creando editorial...', 'info');
    
    try {
        const response = await fetch('/api/editoriales', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeModalNuevaEditorial();
            
            // Mensaje según si se analizó o no
            if (result.prioridad !== undefined) {
                showToast(
                    `✅ ${result.message}`, 
                    'success'
                );
            } else if (result.warning) {
                showToast(`⚠️ ${result.warning}`, 'warning');
            } else {
                showToast('✅ Editorial creada exitosamente', 'success');
            }
            
            // Recargar tabla
            await loadEditoriales();
            
            // Si se asignó a un bloque, aplicar filtro
            if (result.bloque) {
                const filtroBloque = document.getElementById('filter-bloque');
                if (filtroBloque) {
                    filtroBloque.value = result.bloque;
                    await loadEditoriales();
                }
            }
        } else {
            showToast(`Error: ${result.error}`, 'error');
        }
        
    } catch (error) {
        console.error('Error creando editorial:', error);
        showToast('Error al crear la editorial', 'error');
    }
}

// Event listener para botón Nueva Editorial
document.addEventListener('DOMContentLoaded', () => {
    const btnNuevaEditorial = document.getElementById('btn-nueva-editorial');
    if (btnNuevaEditorial) {
        btnNuevaEditorial.addEventListener('click', openModalNuevaEditorial);
    }
});

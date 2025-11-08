        // ============================================
// VARIABLES GLOBALES
// ============================================
let currentPlantData = null;
let misEjemplares = [];
let ejemplarSeleccionado = null;
let cameraOn = true;

// ============================================
// ELEMENTOS DEL DOM
// ============================================
const modal = document.getElementById('modalAgregarPlanta');
const closeBtn = document.querySelector('.close');
const video = document.getElementById('videoStream');
const toggleBtn = document.getElementById('toggleCameraBtn');

// ============================================
// FUNCIONES AUXILIARES
// ============================================

/**
 * Muestra una notificación temporal
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de notificación ('success' o 'error')
 */
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.style.display = 'block';

    setTimeout(() => {
        notification.style.display = 'none';
    }, 3000);
}

/**
 * Obtiene el token CSRF de Django
 * @returns {string} Token CSRF
 */
function getCSRFToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

/**
 * Verifica si la planta detectada es válida
 * @param {object} data - Datos de la planta
 * @returns {boolean} True si es una planta válida
 */
function esPlantaValida(data) {
    return data.label &&
           data.label !== "Detectando..." &&
           data.label !== "Desconocido" &&
           data.label !== "no_planta";
}

// ============================================
// ACTUALIZACIÓN DE INFORMACIÓN DE PLANTA
// ============================================

/**
 * Actualiza toda la información de la planta en la interfaz
 */
function updatePlantInfo() {
    fetch(window.GET_PLANT_DATA_URL)
        .then(response => response.json())
        .then(data => {
            currentPlantData = data;
            actualizarNombrePlanta(data);
            actualizarInfoTaxonomica(data);
            actualizarAnalisisColor(data);
            actualizarInfoEspecie(data);

            // Guardar ejemplares del usuario (si los tiene)
            if (data.mis_ejemplares) {
                misEjemplares = data.mis_ejemplares;
            }
        })
        .catch(error => console.error('Error al obtener los datos de la planta:', error));
}

/**
 * Actualiza el nombre de la planta y botones relacionados
 */
function actualizarNombrePlanta(data) {
    const plantNameDiv = document.querySelector('.plant-name');
    const btnGuardar = document.getElementById('guardarPlanta');
    const btnConsejos = document.getElementById('verConsejosBtn');

    const plantaValida = esPlantaValida(data);

    if (plantaValida) {
        plantNameDiv.textContent = `${data.label} (${(data.prob * 100).toFixed(1)}%)`;
        btnGuardar.style.display = 'block';
        if (btnConsejos) btnConsejos.style.display = 'block';
    } else {
        plantNameDiv.textContent = data.label || "Detectando...";
        btnGuardar.style.display = 'none';
        if (btnConsejos) btnConsejos.style.display = 'none';
    }
}

/**
 * Actualiza la información taxonómica (nombre científico y familia)
 */
function actualizarInfoTaxonomica(data) {
    const nombreCientifico = document.getElementById('nombre-cientifico');
    const familia = document.getElementById('familia');

    if (data.nombre_cientifico && data.nombre_cientifico !== '-' && data.nombre_cientifico !== '') {
        nombreCientifico.textContent = data.nombre_cientifico;
        nombreCientifico.style.fontStyle = 'italic';
    } else {
        nombreCientifico.textContent = '-';
        nombreCientifico.style.fontStyle = 'normal';
    }

    if (data.familia && data.familia !== '-' && data.familia !== '') {
        familia.textContent = data.familia;
    } else {
        familia.textContent = '-';
    }
}

/**
 * Actualiza el análisis de color y estado de la planta
 */
function actualizarAnalisisColor(data) {
    if (data.porcentaje_verde !== undefined) {
        document.getElementById('color-verde').textContent = data.porcentaje_verde.toFixed(1) + '%';
        document.getElementById('color-amarillo').textContent = data.porcentaje_amarillo.toFixed(1) + '%';
        document.getElementById('color-marron').textContent = data.porcentaje_marron.toFixed(1) + '%';
        document.getElementById('color-rojo').textContent = data.porcentaje_rojo.toFixed(1) + '%';

        const estadoDiv = document.getElementById('estado-color');
        estadoDiv.textContent = data.descripcion_estado || 'Analizando...';
        estadoDiv.className = data.estado === 1 ? 'estado-badge saludable' : 'estado-badge atencion';
    }
}

/**
 * Actualiza la información de la especie en la sección inferior
 */
function actualizarInfoEspecie(data) {
    const speciesName = document.querySelector('.species-name');
    const speciesText = document.querySelector('.species-text');
    const speciesImg = document.querySelector('.species-image img');
    const refLink = document.querySelector('.species-reference a');
    const plantaValida = esPlantaValida(data);

    if (plantaValida) {
        speciesName.textContent = data.label;
        speciesText.textContent = data.descripcion || 'No hay descripción disponible para esta especie.';

        if (data.imagen) {
            speciesImg.src = data.imagen;
            speciesImg.alt = data.label;
        }

        if (data.referencia) {
            refLink.href = data.referencia;
            refLink.textContent = 'Ver más información';
        }
    } else if (data.label === "no_planta") {
        speciesName.textContent = "no_planta";
        speciesText.textContent = data.descripcion || "Especie detectada pero no está en el catálogo.";
        speciesImg.src = "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=280&h=320&fit=crop";
        speciesImg.alt = "Planta";
        refLink.href = "https://es.wikipedia.org/wiki/Planta";
        refLink.textContent = "Ver más información";
    } else {
        speciesName.textContent = "Detectando...";
        speciesText.textContent = "La información aparecerá cuando se detecte una planta.";
        speciesImg.src = "https://images.unsplash.com/photo-1614594975525-e45190c55d0b?w=280&h=320&fit=crop";
        speciesImg.alt = "Planta";
        refLink.href = "https://es.wikipedia.org/wiki/Planta";
        refLink.textContent = "Ver más información";
    }
}

// ============================================
// GESTIÓN DEL MODAL
// ============================================

/**
 * Abre el modal para guardar/actualizar planta
 */
async function abrirModal() {
    if (!currentPlantData) {
        showNotification('No hay datos de planta para guardar', 'error');
        return;
    }

    // Pre-llenar datos de color
    document.getElementById('previewVerde').textContent = currentPlantData.porcentaje_verde.toFixed(1) + '%';
    document.getElementById('previewAmarillo').textContent = currentPlantData.porcentaje_amarillo.toFixed(1) + '%';
    document.getElementById('previewMarron').textContent = currentPlantData.porcentaje_marron.toFixed(1) + '%';
    document.getElementById('previewRojo').textContent = currentPlantData.porcentaje_rojo.toFixed(1) + '%';
    document.getElementById('previewEstado').textContent = currentPlantData.descripcion_estado || 'Estado desconocido';

    // Verificar si el usuario ya tiene ejemplares de esta especie
    if (currentPlantData.tiene_ejemplares && misEjemplares.length > 0) {
        mostrarSeccionEjemplares();
    } else {
        ocultarSeccionEjemplares();
    }

    modal.style.display = 'block';
}

/**
 * Muestra la sección de ejemplares existentes
 */
function mostrarSeccionEjemplares() {
    document.getElementById('seccionEjemplares').style.display = 'block';
    document.getElementById('modalTitle').textContent = '🌱 Actualizar o Crear Ejemplar';

    const listaHTML = misEjemplares.map(e => `
        <div class="ejemplar-item" data-id="${e.id}">
            <strong>${currentPlantData.label} #${e.id}</strong>
            <br><small style="color: #888;">Estado: ${e.estado === 1 ? 'Saludable' : 'Necesita atención'}</small>
        </div>
    `).join('');

    document.getElementById('ejemplaresList').innerHTML = listaHTML;

    // Agregar event listeners a los ejemplares
    document.querySelectorAll('.ejemplar-item').forEach(item => {
        item.addEventListener('click', function() {
            document.querySelectorAll('.ejemplar-item').forEach(i => i.classList.remove('selected'));
            this.classList.add('selected');
            ejemplarSeleccionado = this.dataset.id;
            document.getElementById('plantaIdActualizar').value = ejemplarSeleccionado;
            document.getElementById('btnSubmit').textContent = '🔄 Actualizar Monitoreo';
        });
    });
}

/**
 * Oculta la sección de ejemplares (para crear nuevo directamente)
 */
function ocultarSeccionEjemplares() {
    document.getElementById('seccionEjemplares').style.display = 'none';
    document.getElementById('modalTitle').textContent = '🌱 Guardar Nueva Planta';
    document.getElementById('btnSubmit').textContent = '💾 Guardar Planta';
}

/**
 * Cierra el modal y resetea el formulario
 */
function cerrarModal() {
    modal.style.display = 'none';
    document.getElementById('formAgregarPlanta').reset();
    ejemplarSeleccionado = null;
    document.getElementById('plantaIdActualizar').value = '';
}

/**
 * Maneja el cambio del checkbox "Crear nuevo"
 */
function manejarCheckboxCrearNuevo(checked) {
    if (checked) {
        document.getElementById('plantaIdActualizar').value = '';
        ejemplarSeleccionado = null;
        document.querySelectorAll('.ejemplar-item').forEach(i => i.classList.remove('selected'));
        document.getElementById('btnSubmit').textContent = '💾 Crear Nuevo Ejemplar';
    } else {
        document.getElementById('btnSubmit').textContent = '🔄 Actualizar Monitoreo';
    }
}

// ============================================
// GUARDAR PLANTA
// ============================================

/**
 * Envía el formulario para guardar/actualizar la planta
 */
async function guardarPlanta(e) {
    e.preventDefault();

    const btn = document.querySelector('.btn-submit');
    btn.disabled = true;
    const textoOriginal = btn.textContent;
    btn.textContent = '⏳ Guardando...';

    const formData = new FormData();
    formData.append('nombre', currentPlantData.label);
    formData.append('nombre_cientifico', currentPlantData.nombre_cientifico || '');
    formData.append('familia', currentPlantData.familia || '');
    formData.append('descripcion', currentPlantData.descripcion || '');
    formData.append('imagen_url', currentPlantData.imagen || '');

    // ID del ejemplar (para actualizar existente)
    const plantaId = document.getElementById('plantaIdActualizar').value;
    if (plantaId) {
        formData.append('planta_id', plantaId);
    }

    // Datos del monitoreo
    formData.append('porcentaje_verde', currentPlantData.porcentaje_verde);
    formData.append('porcentaje_amarillo', currentPlantData.porcentaje_amarillo);
    formData.append('porcentaje_marron', currentPlantData.porcentaje_marron);
    formData.append('porcentaje_rojo', currentPlantData.porcentaje_rojo);
    formData.append('estado', currentPlantData.estado);
    formData.append('descripcion_estado', currentPlantData.descripcion_estado);

    try {
        const response = await fetch(window.GUARDAR_PLANTA_URL, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            },
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            showNotification(result.message, 'success');
            cerrarModal();
            updatePlantInfo(); // Recargar ejemplares
        } else {
            showNotification('Error: ' + result.message, 'error');
        }
    } catch (error) {
        showNotification('Error al guardar: ' + error, 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = textoOriginal;
    }
}

// ============================================
// CONTROL DE CÁMARA
// ============================================

/**
 * Enciende o apaga la cámara
 */
function toggleCamera() {
    if (cameraOn) {
        video.src = video.dataset.placeholder;
        toggleBtn.textContent = "Encender cámara";
        toggleBtn.classList.add('off');
        cameraOn = false;
    } else {
        video.src = window.VIDEO_FEED_URL;
        toggleBtn.textContent = "Apagar cámara";
        toggleBtn.classList.remove('off');
        cameraOn = true;
    }
}

// ============================================
// EVENT LISTENERS
// ============================================

/**
 * Inicializa todos los event listeners
 */
function initEventListeners() {
    // Botón guardar planta
    document.getElementById('guardarPlanta').addEventListener('click', abrirModal);

    // Cerrar modal
    closeBtn.onclick = cerrarModal;

    // Cerrar modal al hacer clic fuera
    window.onclick = function(event) {
        if (event.target == modal) {
            cerrarModal();
        }
    };

    // Checkbox "Crear nuevo"
    document.getElementById('crearNuevo').addEventListener('change', function() {
        manejarCheckboxCrearNuevo(this.checked);
    });

    // Enviar formulario
    document.getElementById('formAgregarPlanta').addEventListener('submit', guardarPlanta);

    // Control de cámara
    toggleBtn.addEventListener('click', toggleCamera);
}

// ============================================
// INICIALIZACIÓN
// ============================================

/**
 * Inicializa la aplicación cuando el DOM está listo
 */
function init() {
    initEventListeners();
    updatePlantInfo();

    // Actualiza cada 2 segundos
    setInterval(updatePlantInfo, 2000);
}

// Ejecutar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}
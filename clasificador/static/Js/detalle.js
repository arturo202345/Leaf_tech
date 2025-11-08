let monitoreoActualId = null;

function abrirModalNotas(monitoreoId, notasActuales) {
    monitoreoActualId = monitoreoId;
    const modal = document.getElementById('modalNotas');
    const textarea = document.getElementById('notasTexto');
    const titulo = document.getElementById('modalTitulo');
    const form = document.getElementById('formNotas');

    // Configurar título y acción del formulario
    if (notasActuales && notasActuales !== 'None') {
        titulo.textContent = 'Editar Nota';
        textarea.value = notasActuales;
    } else {
        titulo.textContent = 'Agregar Nota';
        textarea.value = '';
    }

    // Actualizar contador de caracteres
    actualizarContador();

    // Configurar URL del formulario
    form.action = `/planta/monitoreo/${monitoreoId}/nota/`;

    modal.style.display = 'block';
    textarea.focus();
}

function cerrarModalNotas() {
    const modal = document.getElementById('modalNotas');
    modal.style.display = 'none';
    monitoreoActualId = null;
}

function actualizarContador() {
    const textarea = document.getElementById('notasTexto');
    const contador = document.getElementById('contadorCaracteres');
    const longitud = textarea.value.length;
    contador.textContent = longitud;

    // Cambiar color si se acerca al límite
    if (longitud > 450) {
        contador.style.color = '#e74c3c';
    } else if (longitud > 400) {
        contador.style.color = '#f39c12';
    } else {
        contador.style.color = '#95a5a6';
    }
}

// Event listeners
document.addEventListener('DOMContentLoaded', function() {
    const textarea = document.getElementById('notasTexto');

    // Contador de caracteres
    textarea.addEventListener('input', actualizarContador);

    // Límite de caracteres
    textarea.addEventListener('input', function() {
        if (this.value.length > 500) {
            this.value = this.value.substring(0, 500);
            actualizarContador();
        }
    });

    // Cerrar modal al hacer clic fuera
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('modalNotas');
        if (event.target === modal) {
            cerrarModalNotas();
        }
    });

    // Cerrar modal con Escape
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            cerrarModalNotas();
        }
    });
});

function confirmarEliminar() {
    if (confirm('¿Estás seguro de que deseas eliminar este ejemplar? Esta acción no se puede deshacer.')) {
        window.location.href = "{% url 'eliminar_planta' planta.id %}";
    }
}


// mis plantas
// Búsqueda de plantas
document.getElementById('searchInput').addEventListener('keyup', function() {
    const searchValue = this.value.toLowerCase();
    const plantCards = document.querySelectorAll('.plant-card');

    plantCards.forEach(card => {
        const plantName = card.getAttribute('data-name');
        if (plantName.includes(searchValue)) {
            card.style.display = 'block';
        } else {
            card.style.display = 'none';
        }
    });
});
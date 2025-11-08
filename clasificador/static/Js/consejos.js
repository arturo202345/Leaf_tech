let modalConsejos = document.getElementById('modalConsejos');
let closeConsejos = document.querySelector('.close-consejos');
let btnVerConsejos = document.getElementById('verConsejosBtn');

// Iconos SVG para dificultad y toxicidad (solo paths)
const iconPaths = {
    check: 'M20 6L9 17l-5-5',
    alerta: 'M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0zM12 9v4m0 4h.01',
    calavera: '',
    sonrisa: 'M8 14s1.5 2 4 2 4-2 4-2M9 9h.01M15 9h.01',
    pensativo: 'M8 15h8M9 9h.01M15 9h.01',
    preocupado: 'M16 16s-1.5-2-4-2-4 2-4 2M9 9h.01M15 9h.01'
};

// FUNCIÓN PRINCIPAL PARA MOSTRAR CONSEJOS
async function mostrarConsejos() {
    if (!currentPlantData || !currentPlantData.label ||
        currentPlantData.label === "Detectando..." ||
        currentPlantData.label === "no_planta") {
        showNotification('No hay planta detectada para mostrar consejos', 'error');
        return;
    }

    modalConsejos.style.display = 'block';

    // Ocultar todo y mostrar loading
    document.getElementById('consejosLoading').style.display = 'block';
    document.getElementById('noConsejos').style.display = 'none';
    document.getElementById('errorConsejos').style.display = 'none';

    // Limpiar contenido anterior del template
    const oldContent = document.querySelector('.consejos-header');
    if (oldContent) oldContent.parentElement.remove();

    try {
        let response = await fetch(`/get-consejos-cuidado/?nombre_planta=${encodeURIComponent(currentPlantData.label)}`);
        let data = await response.json();

        // Ocultar loading
        document.getElementById('consejosLoading').style.display = 'none';

        if (data.success) {
            let c = data.consejos;

            // Clonar template
            const template = document.getElementById('consejosTemplate');
            const clone = template.content.cloneNode(true);

            // Llenar datos básicos
            clone.getElementById('nombrePlanta').textContent = c.nombre_planta;

            if (c.nombre_cientifico) {
                const cientificoEl = clone.getElementById('nombreCientifico');
                cientificoEl.textContent = c.nombre_cientifico;
                cientificoEl.style.display = 'block';
            }

            // Dificultad
            const badgeDif = clone.getElementById('badgeDificultad');
            badgeDif.className = `consejo-badge badge-${c.dificultad.toLowerCase()}`;
            clone.getElementById('iconDificultad').setAttribute('d', iconPaths[c.dificultad_svg] || iconPaths.pensativo);
            clone.getElementById('textoDificultad').textContent = c.dificultad;

            // Toxicidad
            clone.getElementById('iconToxicidad').setAttribute('d', iconPaths[c.toxicidad_svg] || iconPaths.check);
            clone.getElementById('textoToxicidad').textContent = c.toxicidad;

            // Contenido de consejos
            clone.getElementById('conLuz').textContent = c.luz;
            clone.getElementById('conRiego').textContent = c.riego;
            clone.getElementById('conTemperatura').textContent = c.temperatura;
            clone.getElementById('conHumedad').textContent = c.humedad;
            clone.getElementById('conSuelo').textContent = c.suelo;
            clone.getElementById('conFertilizacion').textContent = c.fertilizacion;

            // Opcionales
            if (c.poda) {
                const itemPoda = clone.getElementById('itemPoda');
                itemPoda.style.display = 'block';
                clone.getElementById('conPoda').textContent = c.poda;
            }

            if (c.plagas_comunes) {
                const itemPlagas = clone.getElementById('itemPlagas');
                itemPlagas.style.display = 'block';
                clone.getElementById('conPlagas').textContent = c.plagas_comunes;
            }

            if (c.notas_adicionales) {
                const itemNotas = clone.getElementById('itemNotas');
                itemNotas.style.display = 'block';
                clone.getElementById('conNotas').textContent = c.notas_adicionales;
            }

            // Insertar en el DOM
            document.getElementById('consejosContent').appendChild(clone);
        } else {
            // No hay consejos disponibles
            const noConsejos = document.getElementById('noConsejos');
            document.getElementById('mensajeNoConsejos').textContent = data.message;
            noConsejos.style.display = 'block';
        }
    } catch (error) {
        document.getElementById('consejosLoading').style.display = 'none';
        document.getElementById('errorConsejos').style.display = 'block';
        console.error('Error:', error);
    }
}

// ============================================
// EVENT LISTENERS
// ============================================
closeConsejos.onclick = () => modalConsejos.style.display = 'none';

window.addEventListener('click', (e) => {
    if (e.target == modalConsejos) modalConsejos.style.display = 'none';
});

btnVerConsejos.addEventListener('click', mostrarConsejos);

// ============================================
// MODIFICAR updatePlantInfo PARA CONTROLAR BOTÓN
// ============================================
const updatePlantInfoOriginal = updatePlantInfo;
updatePlantInfo = function() {
    updatePlantInfoOriginal();

    if (currentPlantData) {
        const esPlantaValida = currentPlantData.label &&
                               currentPlantData.label !== "Detectando..." &&
                               currentPlantData.label !== "Desconocido" &&
                               currentPlantData.label !== "no_planta";

        btnVerConsejos.style.display = esPlantaValida ? 'block' : 'none';
    } else {
        btnVerConsejos.style.display = 'none';
    }
}
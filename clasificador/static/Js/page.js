document.addEventListener("DOMContentLoaded", () => {
    console.log("✅ page.js cargado");

    // -----------------------------
    // REFERENCIAS A ELEMENTOS DEL DOM
    // -----------------------------
    const plantName = document.querySelector(".plant-name");
    const nombreCientifico = document.getElementById("nombre-cientifico");
    const familia = document.getElementById("familia");

    const colorVerde = document.getElementById("color-verde");
    const colorAmarillo = document.getElementById("color-amarillo");
    const colorMarron = document.getElementById("color-marron");
    const colorRojo = document.getElementById("color-rojo");
    const estadoColor = document.getElementById("estado-color");

    const guardarBtn = document.getElementById("guardarPlanta");
    const verConsejosBtn = document.getElementById("verConsejosBtn");

    const modal = document.getElementById("modalAgregarPlanta");
    const modalClose = modal.querySelector(".close");
    const modalForm = document.getElementById("formAgregarPlanta");

    const ejemplaresList = document.getElementById("ejemplaresList");
    const seccionEjemplares = document.getElementById("seccionEjemplares");
    const plantaIdActualizar = document.getElementById("plantaIdActualizar");

    const previewVerde = document.getElementById("previewVerde");
    const previewAmarillo = document.getElementById("previewAmarillo");
    const previewMarron = document.getElementById("previewMarron");
    const previewRojo = document.getElementById("previewRojo");
    const previewEstado = document.getElementById("previewEstado");

    const crearNuevo = document.getElementById("crearNuevo");
    const notification = document.getElementById("notification");

    const videoImg = document.getElementById("videoStream");
    const toggleCameraBtn = document.getElementById("toggleCameraBtn");

    // URLs definidas globalmente desde Django
    const GET_PLANT_DATA_URL = window.GET_PLANT_DATA_URL;
    const GUARDAR_PLANTA_URL = window.GUARDAR_PLANTA_URL;
    const VIDEO_FEED_URL = window.VIDEO_FEED_URL;


    // -----------------------------
    // FUNCIÓN PARA MOSTRAR NOTIFICACIONES
    // -----------------------------
    function showNotification(msg, type = "success") {
        if (!notification) return;

        notification.innerText = msg;
        notification.className = "notification show " + type;

        setTimeout(() => {
            notification.classList.remove("show");
        }, 3000);
    }


    // -----------------------------
    // CONSULTA PERIÓDICA: GET DATA
    // -----------------------------
    let updating = false;

    async function actualizarDatos() {
        if (updating) return;
        updating = true;

        try {
            const res = await fetch(GET_PLANT_DATA_URL);
            if (!res.ok) throw new Error("Error al obtener datos");

            const data = await res.json();

            if (!data || !data.nombre) {
                plantName.textContent = "No se detecta planta";
                verConsejosBtn.style.display = "none";
                updating = false;
                return;
            }

            // Nombre común
            plantName.textContent = data.nombre || "Planta detectada";

            // Datos taxonómicos
            if (nombreCientifico) nombreCientifico.textContent = data.nombre_cientifico || "-";
            if (familia) familia.textContent = data.familia || "-";

            // Análisis de color
            function formatPercent(v) {
                return isNaN(v) ? "0%" : `${parseInt(v)}%`;
            }

            colorVerde.textContent = formatPercent(data.verde);
            colorAmarillo.textContent = formatPercent(data.amarillo);
            colorMarron.textContent = formatPercent(data.marron);
            colorRojo.textContent = formatPercent(data.rojo);

            estadoColor.textContent = data.estado_color || "Analizando...";

            // Mostrar botón de consejos solo si hay planta válida
            verConsejosBtn.style.display = "inline-block";

        } catch (err) {
            console.error("❌ Error:", err);
        } finally {
            updating = false;
        }
    }

    setInterval(actualizarDatos, 800);
    actualizarDatos();


    // -----------------------------
    // TOGGLE DE CÁMARA
    // -----------------------------
    let camaraActiva = true;

    toggleCameraBtn.addEventListener("click", () => {
        if (!videoImg) return;

        if (camaraActiva) {
            videoImg.src = videoImg.dataset.placeholder;
            toggleCameraBtn.textContent = "Encender cámara";
        } else {
            videoImg.src = VIDEO_FEED_URL;
            toggleCameraBtn.textContent = "Apagar cámara";
        }

        camaraActiva = !camaraActiva;
    });


    // -----------------------------
    // ABRIR MODAL AL GUARDAR PLANTA
    // -----------------------------
    guardarBtn.addEventListener("click", async () => {
        modal.style.display = "block";

        // Cargar los datos actuales de color en el modal
        previewVerde.textContent = colorVerde.textContent;
        previewAmarillo.textContent = colorAmarillo.textContent;
        previewMarron.textContent = colorMarron.textContent;
        previewRojo.textContent = colorRojo.textContent;
        previewEstado.textContent = estadoColor.textContent;

        await cargarEjemplaresPrevios();
    });

    modalClose.addEventListener("click", () => {
        modal.style.display = "none";
        plantaIdActualizar.value = "";
    });


    // -----------------------------
    // CARGAR EJEMPLARES GUARDADOS DEL USUARIO
    // -----------------------------
    async function cargarEjemplaresPrevios() {
        try {
            const res = await fetch("/mis-plantas/?ajax=1");
            if (!res.ok) throw new Error("Error cargando ejemplares");
            const data = await res.json();

            ejemplaresList.innerHTML = "";
            plantaIdActualizar.value = "";
            crearNuevo.checked = false;

            if (data.ejemplares && data.ejemplares.length > 0) {
                seccionEjemplares.style.display = "block";

                data.ejemplares.forEach(e => {
                    const btn = document.createElement("button");
                    btn.className = "ejemplar-item";
                    btn.dataset.id = e.id;
                    btn.textContent = `✅ ${e.nombre}`;
                    ejemplaresList.appendChild(btn);
                });

            } else {
                seccionEjemplares.style.display = "none";
            }

        } catch (err) {
            console.error(err);
        }
    }


    // Delegación de eventos para seleccionar ejemplar
    ejemplaresList.addEventListener("click", (e) => {
        if (e.target.classList.contains("ejemplar-item")) {
            const id = e.target.dataset.id;
            plantaIdActualizar.value = id;
            crearNuevo.checked = false;

            document.querySelectorAll(".ejemplar-item")
                .forEach(x => x.classList.remove("selected"));

            e.target.classList.add("selected");
        }
    });


    // -----------------------------
    // GUARDAR PLANTA
    // -----------------------------
    modalForm.addEventListener("submit", async (event) => {
        event.preventDefault();

        const formData = new FormData(modalForm);
        formData.append("verde", colorVerde.textContent.replace("%", ""));
        formData.append("amarillo", colorAmarillo.textContent.replace("%", ""));
        formData.append("marron", colorMarron.textContent.replace("%", ""));
        formData.append("rojo", colorRojo.textContent.replace("%", ""));
        formData.append("estado_color", estadoColor.textContent);

        if (crearNuevo.checked) {
            formData.set("planta_id", "");
        }

        try {
            const res = await fetch(GUARDAR_PLANTA_URL, {
                method: "POST",
                headers: { "X-CSRFToken": getCSRFToken() },
                body: formData
            });

            if (!res.ok) throw new Error("Error al guardar");

            const data = await res.json();

            showNotification(data.message || "Planta guardada");
            modal.style.display = "none";

        } catch (err) {
            console.error(err);
            showNotification("No se pudo guardar", "error");
        }
    });


    // -----------------------------
    // CSRF TOKEN
    // -----------------------------
    function getCSRFToken() {
        const input = document.querySelector("input[name='csrfmiddlewaretoken']");
        return input ? input.value : "";
    }
});

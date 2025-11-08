// Función para descargar como PDF
        function descargarPDF() {
            alert('💡 Para descargar como PDF:\n\n1. Haz clic en "Imprimir"\n2. Selecciona "Guardar como PDF"\n3. Elige la ubicación y guarda');
            window.print();
        }

        // Smooth scroll para los enlaces de la tabla de contenidos
        document.querySelectorAll('.toc a').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            });
        });
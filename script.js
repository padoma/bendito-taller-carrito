let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
let productoActual = null;

/* ==========================
   CARGAR PRODUCTO URL
========================== */
function obtenerProductoURL(){
    const params = new URLSearchParams(window.location.search);
    const id = params.get("producto");

    localStorage.setItem(
        "volverCatalogo",
        "https://sites.google.com/view/bendito-taller/p%C3%A1gina-principal"
    );

    if(!id || !productos[id]) return;

    productoActual = productos[id];
    abrirSelectorProducto();
}

/* ==========================
   SELECTOR PRODUCTO (MODAL)
========================== */
function abrirSelectorProducto(){
    const p = productoActual;
    let opcionesHTML = "";

    /* MEDIDAS */
    if(p.tipo === "medidas"){
        opcionesHTML = `
        <div class="modal-input-group">
            <label for="medidaSelect">Medida</label>
            <select id="medidaSelect" class="modal-select">
                ${p.opciones.map(op => `
                    <option value="${op.medida}|${op.mayor}|${op.unitario}">
                        ${op.medida}
                    </option>
                `).join("")}
            </select>
        </div>

        <div class="modal-input-group">
            <label for="tipoCompra">Tipo de compra</label>
            <select id="tipoCompra" class="modal-select">
                <option value="unitario">Unitario</option>
                <option value="mayor">Por Mayor</option>
            </select>
        </div>
        `;
    }

    /* SIMPLE */
    if(p.tipo === "simple"){
        opcionesHTML = `
        <div class="modal-input-group">
            <label for="tipoCompraSimple">Tipo de compra</label>
            <select id="tipoCompraSimple" class="modal-select">
                <option value="unitario|${p.unitario}">
                    Unitario ($${p.unitario.toLocaleString("es-CL")})
                </option>
                <option value="mayor|${p.mayor}">
                    Por Mayor ($${p.mayor.toLocaleString("es-CL")})
                </option>
            </select>
        </div>
        `;
    }

    /* VARIANTES */
    if(p.tipo === "variantes"){
        opcionesHTML = `
        <div class="modal-input-group">
            <label for="varianteSelect">Opción de material / espesor</label>
            <select id="varianteSelect" class="modal-select">
                ${p.opciones.map(op => `
                    <option value="${op.nombre}|${op.precio}">
                        ${op.nombre} ($${op.precio.toLocaleString("es-CL")})
                    </option>
                `).join("")}
            </select>
        </div>
        `;
    }

    const popup = document.createElement("div");
    popup.id = "popupProducto";
    popup.className = "modal-overlay";

    popup.innerHTML = `
    <div class="modal-container">
        <h2>${p.nombre}</h2>
        
        ${opcionesHTML}

        <div class="modal-input-group">
            <label for="cantidadProducto">Cantidad</label>
            <input
                type="number"
                id="cantidadProducto"
                value="1"
                min="1"
                class="modal-input"
            >
        </div>

        <div class="modal-input-group">
            <label for="obsProducto">Observación adicional</label>
            <textarea
                id="obsProducto"
                placeholder="Ej: detalles de grabado, color u otros requisitos (opcional)"
                class="modal-textarea"
            ></textarea>
        </div>

        <button onclick="agregarProducto()" class="modal-btn-primary">
            Agregar al pedido
        </button>

        <button onclick="cerrarPopup()" class="modal-btn-secondary">
            Cancelar
        </button>
    </div>
    `;

    document.body.appendChild(popup);
}

/* ==========================
   AGREGAR PRODUCTO
========================== */
function agregarProducto(){
    const p = productoActual;
    const cantidadVal = parseInt(document.getElementById("cantidadProducto").value) || 1;

    let nuevoProducto = {
        codigo: p.codigo,
        nombre: p.nombre,
        imagen: `https://padoma.github.io/bendito-taller-carrito/${p.imagen}`,
        cantidad: cantidadVal,
        observacion: document.getElementById("obsProducto").value.trim(),
        medida: "",
        tipo: "",
        variante: "",
        precio: 0
    };

    if(p.tipo === "medidas"){
        const data = document.getElementById("medidaSelect").value.split("|");
        const tipo = document.getElementById("tipoCompra").value;

        nuevoProducto.medida = data[0];
        nuevoProducto.tipo = tipo === "mayor" ? "Por Mayor" : "Unitario";
        nuevoProducto.precio = tipo === "mayor" ? parseInt(data[1]) : parseInt(data[2]);
    }

    if(p.tipo === "simple"){
        const data = document.getElementById("tipoCompraSimple").value.split("|");
        nuevoProducto.tipo = data[0] === "mayor" ? "Por Mayor" : "Unitario";
        nuevoProducto.precio = parseInt(data[1]);
    }

    if(p.tipo === "variantes"){
        const data = document.getElementById("varianteSelect").value.split("|");
        nuevoProducto.variante = data[0];
        nuevoProducto.precio = parseInt(data[1]);
        nuevoProducto.tipo = "Unitario"; // Por defecto
    }

    // Si ya existe el producto con los mismos atributos (código, medida, variante, tipo, observación), sumar cantidad
    let existente = carrito.find(item => 
        item.codigo === nuevoProducto.codigo &&
        item.medida === nuevoProducto.medida &&
        item.variante === nuevoProducto.variante &&
        item.tipo === nuevoProducto.tipo &&
        item.observacion === nuevoProducto.observacion
    );

    if (existente) {
        existente.cantidad += nuevoProducto.cantidad;
    } else {
        carrito.push(nuevoProducto);
    }

    guardarCarrito();
    renderCarrito();
    cerrarPopup();
    mostrarToast();

    // Intentar cerrar la pestaña primero (si fue abierta como pestaña nueva / popup)
    setTimeout(() => {
        window.close();
        
        // Fallback: Si no se cerró después de 300ms (bloqueado por navegador), redirigir
        setTimeout(() => {
            const volver = localStorage.getItem("volverCatalogo");
            if(volver){
                if (window.self !== window.top) {
                    window.top.location.href = volver;
                } else {
                    window.location.href = volver;
                }
            }
        }, 300);
    }, 900);
}

/* ==========================
   RENDER CARRITO (SIDEBAR DRAWER)
========================== */
function renderCarrito(){
    let html = "";
    let total = 0;

    carrito.forEach((item, index) => {
        let subtotal = item.precio * item.cantidad;
        total += subtotal;

        let detallesAdicionales = [];
        if (item.medida) detallesAdicionales.push(`Medida: ${item.medida}`);
        if (item.variante) detallesAdicionales.push(`Opción: ${item.variante}`);
        if (item.tipo) detallesAdicionales.push(`${item.tipo}`);

        let detailsString = detallesAdicionales.join(" | ");

        html += `
        <div class="cart-item">
            <img 
                src="${item.imagen}"
                alt="${item.nombre}"
                onerror="this.src='https://via.placeholder.com/90?text=Sin+Foto'"
            >

            <div class="item-info">
                <div class="item-title">${item.nombre}</div>
                <div class="item-detail">${detailsString}</div>
                ${item.observacion ? `<div class="item-detail" style="font-style: italic; color: #8e8076;">Obs: "${item.observacion}"</div>` : ""}
                
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <button onclick="restarCantidad(${index})" style="border: none; background: #e5dacb; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; font-weight: bold; color: #4b372d; font-size: 14px; display: flex; align-items: center; justify-content: center;">-</button>
                        <span style="font-weight: bold; font-size: 14px;">${item.cantidad}</span>
                        <button onclick="sumarCantidad(${index})" style="border: none; background: #e5dacb; width: 24px; height: 24px; border-radius: 50%; cursor: pointer; font-weight: bold; color: #4b372d; font-size: 14px; display: flex; align-items: center; justify-content: center;">+</button>
                    </div>
                    <div class="item-price">$${subtotal.toLocaleString("es-CL")}</div>
                </div>
            </div>
        </div>
        `;
    });

    document.getElementById("cartItems").innerHTML = html || `<div style="text-align: center; color: var(--text-muted); padding: 30px 0; font-size: 15px;">Tu carrito está vacío 🛒</div>`;
    document.getElementById("cartTotal").innerHTML = `<span>Total:</span> <span>$${total.toLocaleString("es-CL")}</span>`;
    document.getElementById("cartButton").innerHTML = `🛒 (${carrito.reduce((acc, i) => acc + i.cantidad, 0)})`;
}

/* ==========================
   CONTROLES DE CANTIDAD DESDE SIDEBAR
========================== */
function sumarCantidad(index) {
    carrito[index].cantidad++;
    guardarCarrito();
    renderCarrito();
}

function restarCantidad(index) {
    carrito[index].cantidad--;
    if (carrito[index].cantidad <= 0) {
        carrito.splice(index, 1);
    }
    guardarCarrito();
    renderCarrito();
}

/* ==========================
   TOAST
========================== */
function mostrarToast(){
    const toast = document.getElementById("toast");
    toast.classList.add("show");

    setTimeout(()=>{
        toast.classList.remove("show");
    }, 2000);
}

/* ==========================
   TOGGLE CARRITO DRAW PANEL
========================== */
function toggleCart(){
    const panel = document.getElementById("cartPanel");
    panel.style.display = panel.style.display === "block" ? "none" : "block";
}

/* ==========================
   VOLVER AL CATÁLOGO
========================== */
function volverCatalogo(){
    const volver = localStorage.getItem("volverCatalogo");
    if(volver){
        if (window.self !== window.top) {
            window.top.location.href = volver;
        } else {
            window.location.href = volver;
        }
    }
}

/* ==========================
   CERRAR POPUP
========================== */
function cerrarPopup(){
    const popup = document.getElementById("popupProducto");
    if(popup){
        popup.remove();
    }
    
    // Si entramos con ?producto=id en la URL, limpiar el parametro para evitar que reabra
    const url = new URL(window.location);
    url.searchParams.delete('producto');
    window.history.replaceState({}, document.title, url.pathname);
}

/* ==========================
   GUARDAR
========================== */
function guardarCarrito(){
    localStorage.setItem("carrito", JSON.stringify(carrito));
}

/* ==========================
   ENVIAR A INSTAGRAM
========================== */
function copiarPedido(){
    if (carrito.length === 0) {
        alert("El carrito está vacío.");
        return;
    }

    let mensaje = `Hola 😊 quiero cotizar estos productos de Bendito Taller:\n\n`;

    carrito.forEach(item => {
        let det = [];
        if (item.medida) det.push(`Medida: ${item.medida}`);
        if (item.variante) det.push(`Opción: ${item.variante}`);
        if (item.tipo) det.push(`${item.tipo}`);
        let detStr = det.length > 0 ? ` (${det.join(" | ")})` : "";

        mensaje += `• ${item.nombre}${detStr}\n`;
        mensaje += `  COD: ${item.codigo}\n`;
        mensaje += `  Cantidad: ${item.cantidad}\n`;
        if (item.observacion) mensaje += `  Nota: "${item.observacion}"\n`;
        mensaje += `  Subtotal: $${(item.precio * item.cantidad).toLocaleString("es-CL")}\n\n`;
    });

    const total = carrito.reduce((acc, item) => acc + (item.precio * item.cantidad), 0);
    mensaje += `💰 Total estimado: $${total.toLocaleString("es-CL")}\n`;

    const obsGeneralVal = document.getElementById("obsGeneral").value.trim();
    if (obsGeneralVal) {
        mensaje += `\nObservaciones generales:\n"${obsGeneralVal}"`;
    }

    navigator.clipboard.writeText(mensaje)
        .then(() => {
            alert("¡Pedido copiado al portapapeles! Abre Instagram para enviarlo.");
            window.open("https://www.instagram.com/bendito_taller_/", "_blank");
        })
        .catch(err => {
            console.error("Error al copiar: ", err);
            // Fallback manual en caso de error
            const t = document.createElement("textarea");
            t.value = mensaje;
            document.body.appendChild(t);
            t.select();
            document.execCommand("copy");
            document.body.removeChild(t);
            alert("¡Pedido copiado! Abre Instagram para enviarlo.");
            window.open("https://www.instagram.com/bendito_taller_/", "_blank");
        });
}

/* ==========================
   VACIAR
========================== */
function vaciarCarrito(){
    if(carrito.length === 0) return;
    if(confirm("¿Vaciar todo tu pedido?")){
        carrito = [];
        guardarCarrito();
        renderCarrito();
    }
}

/* ==========================
   INICIO
========================== */
renderCarrito();
obtenerProductoURL();

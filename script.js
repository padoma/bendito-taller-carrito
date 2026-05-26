let carrito = JSON.parse(localStorage.getItem("carrito")) || [];
let productoActual = null;
let opcionPreseleccionada = "";

// Set de códigos intercambiables normalizados (lowercase, sin caracteres especiales)
const codigosIntercambiablesNorm = new Set([
    "bc4", "co120cm", "co130cm", "co1020cm", "co1030cm", "co11", 
    "co1220cm", "co1230cm", "co13", "co14", "co1520cm", "co1530cm", 
    "co16", "co1720cm", "co1730cm", "co18", "co19", "co220cm", 
    "co230cm", "co20", "co21", "co22", "co23", "co2420cm", "co2430cm", 
    "co2520cm", "co2530cm", "co26", "co2720cm", "co2730cm", "co28", 
    "co2920cm", "co2930cm", "co3", "co30", "co31", "co32", "co3320cm", 
    "co3330cm", "co3420cm", "co3430cm", "co3620cm", "co3630cm", 
    "co37", "co420cm", "co430cm", "co520cm", "co530cm", "co620cm", 
    "co630cm", "co720cm", "co730cm", "co820cm", "co830cm", "co920cm", 
    "co930cm", "cruz1", "cruz2", "setcorazonesmulticapa", "florcora1", 
    "florcora2", "florcora3", "bc1", "bc2", "bc3", "ca120cm", "ca130cm", 
    "ca1020cm", "ca1030cm", "ca11trio", "ca123mm", "ca1255mm", 
    "ca133mm", "ca1355mm", "ca14", "ca15", "ca1620cm", "ca1630cm", 
    "ca1720cm", "ca1730cm", "ca18", "ca220cm", "ca230cm", "ca420cm", 
    "ca430cm", "ca520cm", "ca530cm", "ca620cm", "ca630cm", "ca7", 
    "ca8", "ca9trio"
]);

/* ==========================
   HELPERS DE NORMALIZACIÓN
========================== */
function obtenerCodigoItemNormalizado(item) {
    let raw = item.codigo;
    if (item.medida) {
        raw += "_" + item.medida;
    } else if (item.variante) {
        raw += "_" + item.variante;
    }
    return raw.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function esItemIntercambiable(itemNorm) {
    return codigosIntercambiablesNorm.has(itemNorm);
}

function esMedida30cm(itemNorm) {
    return itemNorm.includes("30cm");
}

/* ==========================
   RECALCULAR PRECIOS DEL CARRITO
========================== */
function recalcularPreciosCarrito() {
    let totalGeneral = 0;
    let total30cm = 0;

    // Primer paso: Contar cantidades acumuladas de grupos intercambiables
    carrito.forEach(item => {
        const norm = obtenerCodigoItemNormalizado(item);
        if (esItemIntercambiable(norm)) {
            if (esMedida30cm(norm)) {
                total30cm += item.cantidad;
            } else {
                totalGeneral += item.cantidad;
            }
        }
    });

    // Segundo paso: Actualizar precios unitarios en caliente
    carrito.forEach(item => {
        const norm = obtenerCodigoItemNormalizado(item);
        let aplicaMayorista = false;

        if (esItemIntercambiable(norm)) {
            aplicaMayorista = esMedida30cm(norm) ? (total30cm >= 4) : (totalGeneral >= 4);
        } else {
            // Regla por defecto para productos no intercambiables (4+ de la misma referencia exacta)
            aplicaMayorista = (item.cantidad >= 4);
        }

        item.precio = aplicaMayorista ? item.mayor : item.unitario;
        item.tipo = (aplicaMayorista && item.mayor < item.unitario) ? "Por Mayor" : "Unitario";
    });
}

/* ==========================
   CANTIDAD DE INTERCAMBIABLES EN CARRITO (PARA MODAL)
========================== */
function obtenerCantidadIntercambiablesEnCart(es30cm) {
    let total = 0;
    carrito.forEach(item => {
        const norm = obtenerCodigoItemNormalizado(item);
        if (esItemIntercambiable(norm)) {
            if (esMedida30cm(norm) === es30cm) {
                total += item.cantidad;
            }
        }
    });
    return total;
}

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

    // Si es un alias/redirección a un producto padre agrupado
    if (productos[id].parent) {
        opcionPreseleccionada = productos[id].preselect;
        productoActual = productos[productos[id].parent];
    } else {
        opcionPreseleccionada = "";
        productoActual = productos[id];
    }
    
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
            <select id="medidaSelect" class="modal-select" onchange="actualizarPreciosModal()">
                ${p.opciones.map(op => {
                    const selected = (opcionPreseleccionada && op.medida.toLowerCase().replace(/[^a-z0-9]/g, "") === opcionPreseleccionada.toLowerCase().replace(/[^a-z0-9]/g, "")) ? "selected" : "";
                    return `
                    <option value="${op.medida}|${op.mayor}|${op.unitario}" ${selected}>
                        ${op.medida}
                    </option>
                    `;
                }).join("")}
            </select>
        </div>
        `;
    }

    /* VARIANTES */
    if(p.tipo === "variantes"){
        opcionesHTML = `
        <div class="modal-input-group">
            <label for="varianteSelect">Opción de material / espesor</label>
            <select id="varianteSelect" class="modal-select" onchange="actualizarPreciosModal()">
                ${p.opciones.map(op => `
                    <option value="${op.nombre}|${op.precio}">
                        ${op.nombre}
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
        
        <div id="modalPreciosInfo"></div>

        <div class="modal-input-group">
            <label for="cantidadProducto">Cantidad</label>
            <input
                type="number"
                id="cantidadProducto"
                value="1"
                min="1"
                class="modal-input"
                oninput="actualizarPreciosModal()"
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
    actualizarPreciosModal(); // Inicializar precios dinámicos
}

/* ==========================
   ACTUALIZAR PRECIOS DINÁMICOS MODAL
========================== */
function actualizarPreciosModal() {
    const p = productoActual;
    const container = document.getElementById("modalPreciosInfo");
    if (!container) return;

    let unitario = 0;
    let mayor = 0;
    let tempItem = { codigo: p.codigo, medida: "", variante: "" };

    if (p.tipo === "medidas") {
        const select = document.getElementById("medidaSelect");
        if (select) {
            const data = select.value.split("|");
            tempItem.medida = data[0];
            mayor = parseInt(data[1]);
            unitario = parseInt(data[2]);
        }
    } else if (p.tipo === "simple") {
        unitario = p.unitario;
        mayor = p.mayor || p.unitario;
    } else if (p.tipo === "variantes") {
        const select = document.getElementById("varianteSelect");
        if (select) {
            const data = select.value.split("|");
            tempItem.variante = data[0];
            unitario = parseInt(data[1]);
            mayor = unitario;
        }
    }

    const norm = obtenerCodigoItemNormalizado(tempItem);
    const esInter = esItemIntercambiable(norm);
    const es30 = esMedida30cm(norm);
    
    // Obtener cantidad que ya está en el carrito
    const yaEnCart = esInter ? obtenerCantidadIntercambiablesEnCart(es30) : 0;
    const inputCantidad = parseInt(document.getElementById("cantidadProducto").value) || 1;
    const totalCantidad = yaEnCart + inputCantidad;

    let aplicaMayorista = false;
    if (esInter) {
        aplicaMayorista = (totalCantidad >= 4);
    } else {
        aplicaMayorista = (inputCantidad >= 4);
    }

    let activePrice = aplicaMayorista ? mayor : unitario;

    if (mayor && mayor < unitario) {
        let badgeHTML = "";
        
        if (aplicaMayorista) {
            if (esInter && yaEnCart > 0) {
                badgeHTML = `<div style="font-weight: 600; color: #2e7d32; margin-top: 4px; font-size: 13px;">🎉 ¡Precio Mayorista aplicado! (Combinando con tu carrito)</div>`;
            } else {
                badgeHTML = `<div style="font-weight: 600; color: #2e7d32; margin-top: 4px; font-size: 13px;">🎉 ¡Precio Mayorista aplicado! (Llevas 4+ unidades)</div>`;
            }
        } else {
            if (esInter) {
                if (yaEnCart > 0) {
                    badgeHTML = `<div style="font-weight: 500; color: var(--text-muted); margin-top: 4px; font-size: 13px;">Llevas <span style="font-weight:700; color: var(--primary-color);">${yaEnCart}</span> en tu carrito. Agrega <span style="font-weight:700; color: var(--primary-color);">${4 - totalCantidad}</span> más para activar Mayorista ($${mayor.toLocaleString("es-CL")} c/u)</div>`;
                } else {
                    badgeHTML = `<div style="font-weight: 500; color: var(--text-muted); margin-top: 4px; font-size: 13px;">✨ Combina <span style="color: var(--primary-color); font-weight: 700;">4 o más</span> de esta categoría para activar Mayorista: <span style="color: var(--primary-color); font-weight: 700;">$${mayor.toLocaleString("es-CL")}</span> c/u</div>`;
                }
            } else {
                badgeHTML = `<div style="font-weight: 500; color: var(--text-muted); margin-top: 4px; font-size: 13px;">✨ Llevando <span style="color: var(--primary-color); font-weight: 700;">4 o más</span>: <span style="color: var(--primary-color); font-weight: 700;">$${mayor.toLocaleString("es-CL")}</span> c/u</div>`;
            }
        }

        container.innerHTML = `
        <div style="background: rgba(125, 139, 99, 0.08); border: 1px dashed var(--primary-color); border-radius: 16px; padding: 12px; margin-bottom: 18px; text-align: center; font-size: 14px;">
            <div style="font-weight: 700; color: var(--text-main); font-size: 15px;">🏷️ Precio: $${activePrice.toLocaleString("es-CL")} c/u</div>
            ${badgeHTML}
        </div>
        `;
    } else if (unitario) {
        container.innerHTML = `
        <div style="background: rgba(75, 55, 45, 0.04); border: 1px solid var(--border-color); border-radius: 16px; padding: 12px; margin-bottom: 18px; text-align: center; font-size: 14px;">
            <div style="font-weight: 700; color: var(--text-main); font-size: 15px;">Valor: $${unitario.toLocaleString("es-CL")}</div>
        </div>
        `;
    }
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
        variante: "",
        unitario: p.unitario,
        mayor: p.mayor || p.unitario,
        precio: 0,
        tipo: ""
    };

    if(p.tipo === "medidas"){
        const data = document.getElementById("medidaSelect").value.split("|");
        nuevoProducto.medida = data[0];
        nuevoProducto.mayor = parseInt(data[1]);
        nuevoProducto.unitario = parseInt(data[2]);
    }

    if(p.tipo === "variantes"){
        const data = document.getElementById("varianteSelect").value.split("|");
        nuevoProducto.variante = data[0];
        nuevoProducto.unitario = parseInt(data[1]);
        nuevoProducto.mayor = parseInt(data[1]);
    }

    // Si ya existe el producto con los mismos atributos, sumar cantidad
    let existente = carrito.find(item => 
        item.codigo === nuevoProducto.codigo &&
        item.medida === nuevoProducto.medida &&
        item.variante === nuevoProducto.variante &&
        item.observacion === nuevoProducto.observacion
    );

    if (existente) {
        existente.cantidad += nuevoProducto.cantidad;
    } else {
        carrito.push(nuevoProducto);
    }

    // Recalcular todos los precios antes de guardar
    recalcularPreciosCarrito();
    guardarCarrito();
    renderCarrito();
    cerrarPopup();
    mostrarToast();

    // Intentar cerrar la pestaña primero
    setTimeout(() => {
        window.close();
        
        // Fallback
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

    // Recalcular precios en caliente
    recalcularPreciosCarrito();

    carrito.forEach((item, index) => {
        let subtotal = item.precio * item.cantidad;
        total += subtotal;

        let detallesAdicionales = [];
        if (item.medida) detallesAdicionales.push(`Medida: ${item.medida}`);
        if (item.variante) detallesAdicionales.push(`Opción: ${item.variante}`);
        if (item.tipo === "Por Mayor" && item.mayor < item.unitario) {
            detallesAdicionales.push(`<span style="color: var(--primary-color); font-weight: 600;">Por Mayor</span>`);
        }

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
    recalcularPreciosCarrito();
    guardarCarrito();
    renderCarrito();
}

function restarCantidad(index) {
    carrito[index].cantidad--;
    if (carrito[index].cantidad <= 0) {
        carrito.splice(index, 1);
    }
    recalcularPreciosCarrito();
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
        let precio = item.precio;
        let subtotal = precio * item.cantidad;

        let det = [];
        if (item.medida) det.push(`Medida: ${item.medida}`);
        if (item.variante) det.push(`Opción: ${item.variante}`);
        if (item.tipo === "Por Mayor" && item.mayor < item.unitario) det.push(`Precio Mayorista aplicado`);
        let detStr = det.length > 0 ? ` (${det.join(" | ")})` : "";

        mensaje += `• ${item.nombre}${detStr}\n`;
        mensaje += `  COD: ${item.codigo}\n`;
        mensaje += `  Cantidad: ${item.cantidad}\n`;
        if (item.observacion) mensaje += `  Nota: "${item.observacion}"\n`;
        mensaje += `  Subtotal: $${subtotal.toLocaleString("es-CL")}\n\n`;
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

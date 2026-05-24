let carrito =
JSON.parse(localStorage.getItem("carrito")) || [];

let productoActual = null;

/* ===== CARGAR PRODUCTO DESDE URL ===== */

function obtenerProductoURL(){

    const params =
    new URLSearchParams(window.location.search);

    const id =
    params.get("producto");

    if(!id || !productos[id]) return;

    productoActual = productos[id];

    abrirSelectorProducto();
}

/* ===== POPUP PRODUCTO ===== */

function abrirSelectorProducto(){

    const p = productoActual;

    let opcionesHTML = "";

    if(p.tipo === "medidas"){

        opcionesHTML = `
        <label>Medida</label>

        <select id="medidaSelect">
            ${p.opciones.map(op => `
                <option value="${op.medida}|${op.mayor}|${op.unitario}">
                    ${op.medida}
                    — Mayor $${op.mayor.toLocaleString("es-CL")}
                    / Unitario $${op.unitario.toLocaleString("es-CL")}
                </option>
            `).join("")}
        </select>

        <label>Tipo compra</label>

        <select id="tipoCompra">
            <option value="unitario">
                Unitario
            </option>

            <option value="mayor">
                X Mayor
            </option>
        </select>
        `;
    }

    if(p.tipo === "simple"){

        opcionesHTML = `
        <label>Tipo compra</label>

        <select id="tipoCompraSimple">
            <option value="${p.unitario}">
                Unitario —
                $${p.unitario.toLocaleString("es-CL")}
            </option>

            <option value="${p.mayor}">
                X Mayor —
                $${p.mayor.toLocaleString("es-CL")}
            </option>
        </select>
        `;
    }

    if(p.tipo === "variantes"){

        opcionesHTML = `
        <label>Selecciona opción</label>

        <select id="varianteSelect">
            ${p.opciones.map(op => `
                <option value="${op.nombre}|${op.precio}">
                    ${op.nombre}
                    — $${op.precio.toLocaleString("es-CL")}
                </option>
            `).join("")}
        </select>
        `;
    }

    const popup = document.createElement("div");

    popup.id = "popupProducto";

    popup.innerHTML = `
    <div class="popup-box">

        <img src="${p.imagen}" class="popup-img">

        <h2>${p.nombre}</h2>

        ${opcionesHTML}

        <label>Cantidad</label>

        <input
            type="number"
            id="cantidadProducto"
            value="1"
            min="1"
        >

        <label>Observación</label>

        <textarea
            id="obsProducto"
            placeholder="Opcional">
        </textarea>

        <button
            class="btn-main"
            onclick="agregarProducto()">

            Agregar al pedido

        </button>

        <button
            class="btn-danger"
            onclick="cerrarPopup()">

            Cancelar

        </button>

    </div>
    `;

    document.body.appendChild(popup);
}

/* ===== AGREGAR ===== */

function agregarProducto(){

    const p = productoActual;

    let nuevoProducto = {

        codigo:p.codigo,
        nombre:p.nombre,
        imagen:p.imagen,
        cantidad:parseInt(
            document.getElementById(
                "cantidadProducto"
            ).value
        ),
        observacion:
        document.getElementById(
            "obsProducto"
        ).value

    };

    if(p.tipo==="medidas"){

        let data =
        document.getElementById(
            "medidaSelect"
        ).value.split("|");

        let tipo =
        document.getElementById(
            "tipoCompra"
        ).value;

        nuevoProducto.medida =
        data[0];

        nuevoProducto.tipo =
        tipo;

        nuevoProducto.precio =
        tipo==="mayor"
        ? parseInt(data[1])
        : parseInt(data[2]);
    }

    if(p.tipo==="simple"){

        nuevoProducto.precio =
        parseInt(
            document.getElementById(
                "tipoCompraSimple"
            ).value
        );
    }

    if(p.tipo==="variantes"){

        let data =
        document.getElementById(
            "varianteSelect"
        ).value.split("|");

        nuevoProducto.variante =
        data[0];

        nuevoProducto.precio =
        parseInt(data[1]);
    }

    carrito.push(nuevoProducto);

    guardarCarrito();
    renderCarrito();
    cerrarPopup();
    mostrarToast();
}

/* ===== CARRITO ===== */

function renderCarrito(){

    let html = "";
    let total = 0;

    carrito.forEach(item=>{

        let subtotal =
        item.precio *
        item.cantidad;

        total += subtotal;

        html += `
        <div class="cart-item">

            <img src="${item.imagen}">

            <div class="item-info">

                <div class="item-title">
                    ${item.nombre}
                </div>

                <div class="item-detail">
                    ${item.medida || ""}
                    ${item.variante || ""}
                </div>

                <div class="item-detail">
                    x${item.cantidad}
                </div>

                <div class="item-price">
                    $${subtotal.toLocaleString("es-CL")}
                </div>

            </div>

        </div>
        `;
    });

    document.getElementById(
        "cartItems"
    ).innerHTML = html;

    document.getElementById(
        "cartTotal"
    ).innerHTML =
    `Total:
    $${total.toLocaleString("es-CL")}`;

    document.getElementById(
        "cartButton"
    ).innerHTML =
    `🛒 (${carrito.length})`;
}

/* ===== TOAST ===== */

function mostrarToast(){

    const toast =
    document.getElementById("toast");

    toast.classList.add("show");

    setTimeout(()=>{

        toast.classList.remove("show");

    },2000);
}

/* ===== ABRIR ===== */

function toggleCart(){

    const panel =
    document.getElementById(
        "cartPanel"
    );

    panel.style.display =
    panel.style.display==="block"
    ? "none"
    : "block";
}

/* ===== POPUP ===== */

function cerrarPopup(){

    const popup =
    document.getElementById(
        "popupProducto"
    );

    if(popup){
        popup.remove();
    }
}

/* ===== GUARDAR ===== */

function guardarCarrito(){

    localStorage.setItem(
        "carrito",
        JSON.stringify(carrito)
    );
}

/* ===== INSTAGRAM ===== */

function copiarPedido(){

    let mensaje =
`Hola 😊 quiero cotizar los siguientes productos de Bendito Taller:

`;

    carrito.forEach(item=>{

        mensaje +=
`• ${item.nombre}
COD: ${item.codigo}
${item.medida || ""}
${item.variante || ""}
Cantidad: ${item.cantidad}

`;
    });

    mensaje += `
Observaciones:
${document.getElementById("obsGeneral").value}
`;

    navigator.clipboard.writeText(
        mensaje
    );

    window.open(
        "https://www.instagram.com/bendito_taller_/",
        "_blank"
    );
}

/* ===== VACIAR ===== */

function vaciarCarrito(){

    if(confirm(
        "¿Vaciar carrito?"
    )){

        carrito = [];

        guardarCarrito();
        renderCarrito();
    }
}

/* ===== INICIO ===== */

renderCarrito();
obtenerProductoURL();

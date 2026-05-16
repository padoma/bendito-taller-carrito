let carrito =
JSON.parse(localStorage.getItem("carrito")) || [];

let productoActual = null;

/* ==========================
   CARGAR PRODUCTO URL
========================== */

function obtenerProductoURL(){

    const params =
    new URLSearchParams(window.location.search);

    const id =
    params.get("producto");

    const volver =
    params.get("volver");

    /* guardar URL de regreso */

    if(volver){

        localStorage.setItem(
            "volverCatalogo",
            decodeURIComponent(volver)
        );
    }

    if(!id || !productos[id]) return;

    productoActual =
    productos[id];

    abrirSelectorProducto();
}

/* ==========================
   SELECTOR PRODUCTO
========================== */

function abrirSelectorProducto(){

    const p = productoActual;

    let opcionesHTML = "";

    /* MEDIDAS */

    if(p.tipo === "medidas"){

        opcionesHTML = `

        <label>Medida</label>

        <select id="medidaSelect"
        style="width:100%;
        padding:14px;
        border-radius:14px;
        border:1px solid #ddd;
        margin-bottom:14px;">

            ${p.opciones.map(op => `
                <option value="${op.medida}|${op.mayor}|${op.unitario}">
                    ${op.medida}
                </option>
            `).join("")}

        </select>

        <label>Tipo compra</label>

        <select id="tipoCompra"
        style="width:100%;
        padding:14px;
        border-radius:14px;
        border:1px solid #ddd;">

            <option value="unitario">
                Unitario
            </option>

            <option value="mayor">
                X Mayor
            </option>

        </select>
        `;
    }

    /* SIMPLE */

    if(p.tipo === "simple"){

        opcionesHTML = `

        <label>Tipo compra</label>

        <select id="tipoCompraSimple"
        style="width:100%;
        padding:14px;
        border-radius:14px;
        border:1px solid #ddd;">

            <option value="${p.unitario}">
                Unitario
            </option>

            <option value="${p.mayor}">
                X Mayor
            </option>

        </select>
        `;
    }

    /* VARIANTES */

    if(p.tipo === "variantes"){

        opcionesHTML = `

        <label>Selecciona opción</label>

        <select id="varianteSelect"
        style="width:100%;
        padding:14px;
        border-radius:14px;
        border:1px solid #ddd;">

            ${p.opciones.map(op => `
                <option value="${op.nombre}|${op.precio}">
                    ${op.nombre}
                </option>
            `).join("")}

        </select>
        `;
    }

    const popup =
    document.createElement("div");

    popup.id =
    "popupProducto";

    popup.style = `
        position:fixed;
        inset:0;
        background:rgba(0,0,0,.35);
        display:flex;
        justify-content:center;
        align-items:center;
        z-index:99999;
        padding:20px;
    `;

    popup.innerHTML = `

    <div style="
        background:#fffaf3;
        width:100%;
        max-width:420px;
        border-radius:28px;
        padding:28px;
        box-shadow:0 10px 35px rgba(0,0,0,.15);
    ">

        <h2 style="
            margin:0 0 20px;
            text-align:center;
        ">
            ${p.nombre}
        </h2>

        ${opcionesHTML}

        <label style="
            display:block;
            margin-top:18px;
            margin-bottom:8px;
            font-weight:bold;
        ">
            Cantidad
        </label>

        <input
            type="number"
            id="cantidadProducto"
            value="1"
            min="1"
            style="
                width:100%;
                padding:14px;
                border-radius:14px;
                border:1px solid #ddd;
                font-size:16px;
            "
        >

        <label style="
            display:block;
            margin-top:18px;
            margin-bottom:8px;
            font-weight:bold;
        ">
            Observación
        </label>

        <textarea
            id="obsProducto"
            placeholder="Opcional"
            style="
                width:100%;
                min-height:90px;
                border-radius:14px;
                border:1px solid #ddd;
                padding:12px;
                resize:none;
            "
        ></textarea>

        <button
            onclick="agregarProducto()"
            style="
                width:100%;
                margin-top:20px;
                border:none;
                background:#7d8b63;
                color:white;
                padding:16px;
                border-radius:16px;
                font-size:17px;
                cursor:pointer;
            "
        >
            Agregar al pedido
        </button>

        <button
            onclick="cerrarPopup()"
            style="
                width:100%;
                margin-top:10px;
                border:none;
                background:#c9b8a3;
                color:white;
                padding:16px;
                border-radius:16px;
                font-size:17px;
                cursor:pointer;
            "
        >
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

    const p =
    productoActual;

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

    carrito.push(
        nuevoProducto
    );

    guardarCarrito();
    renderCarrito();
    cerrarPopup();
    mostrarToast();

    /* volver catálogo */

    setTimeout(() => {

        const volver =
        localStorage.getItem(
            "volverCatalogo"
        );

        if(volver){

            window.location.href =
            volver;
        }

    },900);
}

/* ==========================
   RENDER CARRITO
========================== */

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

/* ==========================
   TOAST
========================== */

function mostrarToast(){

    const toast =
    document.getElementById(
        "toast"
    );

    toast.classList.add(
        "show"
    );

    setTimeout(()=>{

        toast.classList.remove(
            "show"
        );

    },2000);
}

/* ==========================
   CARRITO
========================== */

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

/* ==========================
   VOLVER CATÁLOGO
========================== */

function volverCatalogo(){

    const volver =
    localStorage.getItem(
        "volverCatalogo"
    );

    if(volver){

        window.location.href =
        volver;
    }
}

/* ==========================
   CERRAR POPUP
========================== */

function cerrarPopup(){

    const popup =
    document.getElementById(
        "popupProducto"
    );

    if(popup){

        popup.remove();
    }
}

/* ==========================
   GUARDAR
========================== */

function guardarCarrito(){

    localStorage.setItem(
        "carrito",
        JSON.stringify(carrito)
    );
}

/* ==========================
   INSTAGRAM
========================== */

function copiarPedido(){

    let mensaje =
`Hola 😊 quiero cotizar estos productos de Bendito Taller:

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

    mensaje +=
`\nObservaciones:
${document.getElementById("obsGeneral").value}`;

    navigator.clipboard.writeText(
        mensaje
    );

    window.open(
        "https://www.instagram.com/bendito_taller_/",
        "_blank"
    );
}

/* ==========================
   VACIAR
========================== */

function vaciarCarrito(){

    if(confirm(
        "¿Vaciar carrito?"
    )){

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

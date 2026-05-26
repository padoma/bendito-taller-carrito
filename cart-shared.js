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
function recalcularPreciosCarrito(cartArray) {
    const list = cartArray || (typeof carrito !== 'undefined' ? carrito : []);
    let totalGeneral = 0;
    let total30cm = 0;

    // Primer paso: Contar cantidades acumuladas de grupos intercambiables
    list.forEach(item => {
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
    list.forEach(item => {
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

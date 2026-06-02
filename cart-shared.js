// Configuración del contacto de la tienda (número de WhatsApp)
const numeroWhatsapp = "56979295426";

// Set de códigos intercambiables normalizados (lowercase, sin caracteres especiales) - Grupo original de Corazones/Cruces/Altares
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

// Configuración de grupos combinables nuevos
const gruposCombinables = [
    {
        id: "altares_nichos",
        min: 4,
        codigos: [
            "altarvirgencita", "altar1", "altar10", "altar11", "altar2", "altar3", "altar4",
            "altar5", "altar5simple", "altar6", "altar7", "altar8", "altar9",
            "nicho1", "nicho2", "nicho3", "nicho4"
        ]
    },
    {
        id: "virgenes",
        min: 4,
        codigos: ["virgen1", "virgen2", "virgen3", "virgen4"]
    },
    {
        id: "alebrijes_catrinas",
        min: 4,
        codigos: ["alebrije1", "alebrije2", "catrina1", "catrina2"]
    },
    {
        id: "calaveras",
        min: 4,
        codigos: ["cal1", "cal2", "cal3"]
    },
    {
        id: "composiciones_1_3",
        min: 4,
        codigos: ["comp1", "comp2", "comp3"]
    },
    {
        id: "fridas",
        min: 4,
        codigos: ["frida1", "frida2", "frida3", "frida4", "frida5"]
    },
    {
        id: "tienda_vintage",
        min: 4,
        codigos: ["tiendavintage1", "tiendavintage2"]
    },
    {
        id: "grabados_gra",
        min: 4,
        codigos: [
            "gra1", "gra2", "gra3", "gra4", "gra5", "gra6", "gra7", "gra8", "gra9", "gra10",
            "gra11", "gra12", "gra13", "gra14", "gra15", "gra16", "gra17", "gra18", "gra19"
        ]
    },
    {
        id: "set_navideno",
        min: 4,
        codigos: ["setnavideno1", "setnavideno2"]
    },
    {
        id: "casita_muneca_torre",
        min: 4,
        codigos: ["casitamunecas2", "torre"]
    },
    {
        id: "composiciones_4_8_arabesco",
        min: 4,
        codigos: ["arabescofloral1", "comp4", "comp5", "comp6", "comp7", "comp8"]
    },
    {
        id: "set_anillos",
        min: 4,
        codigos: ["setanillos1", "setanillos2", "setanillos3", "setanillos4", "setanillos5", "setanillos6", "setanillos7"]
    },
    {
        id: "deco_infantil",
        min: 4,
        codigos: ["decoinantil1", "decoinfantil2", "decoinantil3", "decoinantil4"]
    },
    {
        id: "animales",
        min: 4,
        codigos: ["chinita", "leopardo", "leopardo2", "tortugahawaiana", "zorrito"]
    },
    {
        id: "abejas_mariposas",
        min: 4,
        codigos: [
            "abejareina",
            "abejareina2",
            "marip1",
            "marip2",
            "marip3",
            "marip4",
            "marip5",
            "marip6",
            "banderinmexicano"
        ]
    },
    {
        id: "cuadros_c",
        min: 4,
        codigos: ["cuadroc1", "cuadroc2", "cuadroc3", "cuadroc4"]
    },
    {
        id: "bienvenidos",
        min: 4,
        codigos: ["bienve1", "bienve2", "bienve3", "bienve4"]
    },
    {
        id: "letreros",
        min: 4,
        codigos: ["letrerovintage", "letrero1", "letrero2", "letrero3", "letrero4"]
    },
    {
        id: "colibri",
        min: 4,
        codigos: ["colibricapas", "colibrigrabado"]
    },
    {
        id: "eclipse",
        min: 4,
        codigos: ["eclipse1", "eclipse2"]
    },
    {
        id: "obras_3d",
        min: 4,
        codigos: [
            "alicia3d", "circo", "halloween", "harrypotter3d", "libromagico1", "libromagico2",
            "narnia3d", "peter3d", "principito1", "principito2", "ratitapresumida", "snoopy1", "snoopy2", "vigendelvalle"
        ]
    },
    {
        id: "corona_navidad_personajes",
        min: 4,
        codigos: ["coronacascanueces", "coronaosito", "coronareno"]
    },
    {
        id: "coronas_navidad_base",
        min: 4,
        codigos: ["cascanuecescapas", "coronacasa", "coronaespecial", "coronasimple", "coronasimple2", "coronavillanavidena"]
    },
    {
        id: "cuadros_navidad",
        min: 4,
        codigos: ["cuadronavideno", "cuadronoel"]
    },
    {
        id: "arboles_navidad_pino",
        min: 3,
        codigos: ["arboldenavidad", "arbolnavideno", "pinohome"]
    },
    {
        id: "cajas_navidad",
        min: 6,
        codigos: ["cajagrinch", "cajasanta"]
    }
];

// Conjuntos de productos no combinables con reglas especiales
const noCombinables3 = new Set([
    "renomecedor", "duodeangeles", "munecodenieve", "tagnavideno", "cascanueces", "renos", "angel3", "caballovintage"
]);

const noCombinables6 = new Set([
    "colganteangelcorazon", "colgantecaballito", "colganteangelestrella", "renograbado", "angel1", "angel2"
]);

/* ==========================
   HELPERS DE NORMALIZACIÓN
========================== */
function obtenerCodigoItemNormalizado(item) {
    if (!item || !item.codigo) return "";
    let raw = item.codigo;
    if (item.medida) {
        raw += "_" + item.medida;
    } else if (item.variante) {
        raw += "_" + item.variante;
    }
    return raw.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function obtenerCodigoBaseNormalizado(item) {
    if (!item || !item.codigo) return "";
    return item.codigo.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function esItemIntercambiable(itemNorm) {
    return codigosIntercambiablesNorm.has(itemNorm);
}

function esMedida30cm(itemNorm) {
    return itemNorm.includes("30cm");
}

function esMedida20cm(itemNorm) {
    return itemNorm.includes("20cm");
}

function esItemAros(normBase) {
    return normBase.startsWith("aros");
}

/* ==========================
   HELPERS DE GRUPOS Y CANTIDADES
========================== */
function obtenerGrupoDeItem(normBase) {
    return gruposCombinables.find(g => g.codigos.includes(normBase)) || null;
}

function obtenerCantidadArosEnCart() {
    const list = typeof carrito !== 'undefined' ? carrito : [];
    let total = 0;
    list.forEach(item => {
        const normBase = obtenerCodigoBaseNormalizado(item);
        if (esItemAros(normBase)) {
            total += item.cantidad;
        }
    });
    return total;
}

function obtenerCantidadGrupoEnCart(groupId) {
    const list = typeof carrito !== 'undefined' ? carrito : [];
    let total = 0;
    list.forEach(item => {
        const normBase = obtenerCodigoBaseNormalizado(item);
        const grp = obtenerGrupoDeItem(normBase);
        if (grp && grp.id === groupId) {
            total += item.cantidad;
        }
    });
    return total;
}

/* ==========================
   RECALCULAR PRECIOS DEL CARRITO
========================== */
function recalcularPreciosCarrito(cartArray) {
    const list = cartArray || (typeof carrito !== 'undefined' ? carrito : []);
    
    // 1. Contadores para los grupos combinables
    let totalIntercambiables30cm = 0;
    let totalIntercambiables20cm = 0;
    let totalIntercambiablesTodo = 0;
    const totalPorGrupo = {};
    gruposCombinables.forEach(g => {
        totalPorGrupo[g.id] = 0;
    });
    let totalAros = 0;

    // Primer paso: Contar cantidades acumuladas
    list.forEach(item => {
        const normFull = obtenerCodigoItemNormalizado(item);
        const normBase = obtenerCodigoBaseNormalizado(item);

        // Grupo original (Corazones/Cruces/Altares/Intercambiables)
        if (esItemIntercambiable(normFull)) {
            if (esMedida30cm(normFull)) {
                totalIntercambiables30cm += item.cantidad;
            } else if (esMedida20cm(normFull)) {
                totalIntercambiables20cm += item.cantidad;
            } else {
                totalIntercambiablesTodo += item.cantidad;
            }
        }

        // Grupos combinables nuevos
        const grp = obtenerGrupoDeItem(normBase);
        if (grp) {
            totalPorGrupo[grp.id] += item.cantidad;
        }

        // Aros
        if (esItemAros(normBase)) {
            totalAros += item.cantidad;
        }
    });

    // Segundo paso: Actualizar precios unitarios en caliente
    list.forEach(item => {
        const normFull = obtenerCodigoItemNormalizado(item);
        const normBase = obtenerCodigoBaseNormalizado(item);
        let aplicaMayorista = false;

        if (esItemAros(normBase)) {
            // Aros tienen lógica de 3 niveles
            item.unitario = 750;
            item.mayor = 400; // Por compatibilidad si se lee mayor en algún lado
            if (totalAros >= 20) {
                item.precio = 400;
                item.tipo = "Por Mayor (20+)";
            } else if (totalAros >= 10) {
                item.precio = 500;
                item.tipo = "Por Mayor (10+)";
            } else {
                item.precio = 750;
                item.tipo = "Unitario";
            }
        } else if (esItemIntercambiable(normFull)) {
            if (esMedida30cm(normFull)) {
                aplicaMayorista = (totalIntercambiables30cm + totalIntercambiablesTodo) >= 4;
            } else if (esMedida20cm(normFull)) {
                aplicaMayorista = (totalIntercambiables20cm + totalIntercambiablesTodo) >= 4;
            } else {
                aplicaMayorista = (totalIntercambiables30cm + totalIntercambiables20cm + totalIntercambiablesTodo) >= 4;
            }
            item.precio = aplicaMayorista ? item.mayor : item.unitario;
            item.tipo = (aplicaMayorista && item.mayor < item.unitario) ? "Por Mayor" : "Unitario";
        } else {
            const grp = obtenerGrupoDeItem(normBase);
            if (grp) {
                // Pertenece a un grupo combinable nuevo
                aplicaMayorista = (totalPorGrupo[grp.id] >= grp.min);
            } else if (noCombinables3.has(normBase)) {
                aplicaMayorista = (item.cantidad >= 3);
            } else if (noCombinables6.has(normBase)) {
                aplicaMayorista = (item.cantidad >= 6);
            } else {
                // Regla por defecto para productos individuales
                aplicaMayorista = (item.cantidad >= 4);
            }

            item.precio = aplicaMayorista ? item.mayor : item.unitario;
            item.tipo = (aplicaMayorista && item.mayor < item.unitario) ? "Por Mayor" : "Unitario";
        }
    });
}

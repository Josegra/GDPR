# 📊 Orígenes y Destinos de la Información — Proceso Compliance LABO2

Este documento resume de forma clara y compacta de **dónde se obtiene la información**, cómo se **procesa** en cada notebook, y **a qué tablas o ficheros destino** se envía dentro del flujo completo del proceso de cumplimiento (Compliance LABO2).

---

## 🧱 1. Estructura general del proceso

El proceso se divide en dos grandes bloques:

- **DATA LOADER** → Carga y normaliza los datos desde las fuentes (NAS, datacap, carbon, etc.) hasta las tablas *diamond*.  
- **FILE GENERATOR** → Genera los ficheros finales (corporate, private, supplier, remarketing, logs y controles).

Ambos forman parte del flujo principal de *compliance* que deja los resultados listos para envío a SG y para auditorías internas.

---

## ⚙️ 2. DATA LOADER

### Notebooks implicados
`00_main`, `complirock_loader`, `complirock_raw_carbon`, `DW_MCorporate`, `DW_MPrivate`

### Flujo general
El **00_main** lanza los dos *loaders* (private y corporate) en paralelo.  
Los notebooks posteriores limpian, validan y cargan la información hacia las tablas intermedias y finales.

### Tabla de orígenes y destinos

| Notebook | Origen de datos | Destino de la información | Descripción |
|-----------|----------------|---------------------------|--------------|
| **complirock_loader** | Diccionario común (funciones de Lilly) + NAS | Entrada para `complirock_raw_carbon` | Recupera variables, valida nombres de ficheros y lanza procesamiento secuencial. |
| **complirock_raw_carbon** | Ficheros `carbon` + Subsidiarias válidas | Tablas `raw` y `carbon` | Procesa cada fichero, formatea fechas (`YYYY-MM-DD`), limpia columnas erróneas y actualiza carbon. |
| **DW_MCorporate** | Tabla `carbon` + Subsidiarias | Tabla `diamond` (corporate) | Filtra por `VALUE_DATE > 6 meses atrás`, cruza con subsidiarias y genera la versión *corporate*. |
| **DW_MPrivate** | Tabla `carbon` + Subsidiarias | Tabla `diamond` (private) | Mismo proceso que corporate, pero para clientes privados. |
| **00_main** | Ejecuta loaders anteriores | Control de ejecución | Lanza ambos loaders y genera resumen del proceso. |

🔸 En resumen:  
`NAS → carbon → diamond`  
donde *diamond* contiene los datos limpios de los últimos seis meses, separados en *corporate* y *private*.

---

## 🧮 3. FILE GENERATOR

### Notebooks implicados
`Labo2_Launcher_v2`, `Labo2_Customers_v2`, `Labo2_Supplier_v2`, `Labo2_CarmarketDealers_v2`, `Labo2_logGenerator_v2`, `Labo2_exhaustivity_control_SG`, `Labo2_deltaGenerator_v2`

### Flujo general
El **Launcher** ejecuta secuencialmente los notebooks de carga (customers, supplier, remarketing) que rellenan las tablas necesarias para generar los ficheros `corporate`, `private` y `supplier`.  
Posteriormente, los notebooks de *log* y *control* gestionan los registros y verificaciones.

### Tabla de orígenes y destinos

| Notebook | Origen de datos | Destino / Salida | Descripción |
|-----------|----------------|------------------|--------------|
| **Labo2_Launcher_v2** | Ejecuta los demás notebooks | Tablas `corporate`, `private`, `supplier` | Coordina toda la generación de datos. Añade país y código de subsidiaria. |
| **Labo2_Customers_v2** | Tabla `dw.dw_customer` (de `datacap`) + `dw.dw_normalization` + contratos | Tabla `diamond.labo2_customer` | Se seleccionan columnas, se cruzan con subsidiarias, se filtran contratos activos y se separan en `private` y `corporate`. |
| **Labo2_Supplier_v2** | Tabla `dw.dw_supplier` + `countries` + `subsidiaries` | Tabla `diamond.labo2_supplier` | Obtiene los últimos datos por cliente, los cruza con subsidiarias y rellena estructura común. |
| **Labo2_CarmarketDealers_v2** | Carpeta `DATAMART/LABO2/RMS` (departamento de remarketing) | Tabla `compli_diamond.labo2_remarketing` | Se lee el último fichero generado, se filtran los IDs más recientes y se estructuran los campos necesarios. |
| **Labo2_logGenerator_v2** | Tabla `LABO2_FILES_T` + CSVs en rutas de ficheros | Ficheros de logs agrupados por tipo | Lee todos los ficheros de `corporate` y `supplier`, filtra los correctos, añade tipo y pivota por fecha. |
| **Labo2_exhaustivity_control_SG** | Tabla `LABO2_FILES_T` + CSVs recientes | Reporte de control de exhaustividad | Compara ficheros actuales y anteriores; si el nuevo crece >20% se notifica por mail a SG. |
| **Labo2_deltaGenerator_v2** | Ficheros generados + diamond tables | Reportes de variación | Genera deltas respecto al periodo anterior (no visible en imágenes pero parte del flujo). |

🔸 En resumen:  
`datacap / dw / RMS → diamond tables → csv final (corporate, private, supplier, remarketing) → logs → reportes`

---

## 🧩 4. Tablas y Ficheros principales

| Tipo de dato | Fuente principal | Tabla / Fichero destino |
|---------------|------------------|--------------------------|
| **Clientes corporate** | `dw_customer` + `contracts` | `diamond.labo2_customer (corporate)` |
| **Clientes privados** | `dw_customer` + `contracts` | `diamond.labo2_customer (private)` |
| **Proveedores** | `dw_supplier` + `countries` | `diamond.labo2_supplier` |
| **Concesionarios / Remarketing** | `DATAMART/LABO2/RMS` | `compli_diamond.labo2_remarketing` |
| **Logs** | `LABO2_FILES_T` + CSVs | Ficheros de log agrupados |
| **Control de exhaustividad** | `LABO2_FILES_T` + CSVs | Reportes (`no_report` o `report`) |
| **Tablas base** | `carbon`, `datacap`, `dw_normalization` | `diamond` (6 meses de datos vigentes) |

---

## 🧠 5. Flujo General Simplificado

```text
NAS / DATACAP / DW SOURCES
           ↓
      DATA LOADER
  (carbon → diamond)
           ↓
      FILE GENERATOR
(customers, supplier, remarketing)
           ↓
 LOG GENERATOR & CONTROL
     (reportes y validaciones)

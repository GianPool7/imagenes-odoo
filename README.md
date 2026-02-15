# External Attachment Storage for Odoo (FastAPI)

## 📌 Descripción

Este proyecto implementa un sistema de almacenamiento externo de archivos para Odoo, utilizando una API desarrollada en FastAPI y un servidor de almacenamiento dedicado (HDD/SSD).

El objetivo es reducir costos de hosting, mejorar el rendimiento de Odoo y evitar que archivos pesados (imágenes, documentos y videos) se almacenen en la base de datos.

---

## ❓ Problema que resuelve

- Odoo guarda los adjuntos (`ir.attachment`) en la base de datos.
- Esto incrementa rápidamente el tamaño de la BD.
- Aumenta el costo del hosting.
- Reduce el rendimiento general del sistema.

---

## ✅ Solución implementada

- Los archivos se almacenan en un servidor externo mediante una File API.
- Odoo guarda únicamente la URL del archivo (peso 0).
- Las imágenes se visualizan inline en el chatter.
- Si la API no está disponible, la subida se bloquea y se muestra un mensaje claro al usuario.

---

## 🏗 Arquitectura

Usuario
↓
Odoo (override ir.attachment)
↓
FastAPI (File API)
↓
Servidor de almacenamiento (HDD / SSD)



---

## 🔐 Seguridad

- Autenticación mediante API Token (`X-API-KEY`)
- Validación de tipo MIME y tamaño máximo por archivo
- Health check antes de cada subida

### Variables de entorno recomendadas

- `BASE_STORAGE_PATH`: ruta base de archivos (default: `/data/files`)
- `BASE_URL`: URL pública para construir links de descarga
- `REQUIRE_API_TOKEN`: `true` o `false` (default: `true`)
- `API_TOKEN`: token esperado en header `X-API-KEY` (obligatorio si `REQUIRE_API_TOKEN=true`)

Ejemplo local sin token:

```bash
export BASE_STORAGE_PATH=./data/files
export BASE_URL=http://127.0.0.1:8000
export REQUIRE_API_TOKEN=false
uvicorn app.main:app --reload
```

Ejemplo producción con token:

```bash
export BASE_STORAGE_PATH=/data/files
export BASE_URL=https://files.tudominio.com
export REQUIRE_API_TOKEN=true
export API_TOKEN='cambia_esto_por_un_token_fuerte'
gunicorn -k uvicorn.workers.UvicornWorker -w 2 -b 0.0.0.0:8000 app.main:app
```

---

## ⚙️ Funcionalidades

- Subida de imágenes, documentos y videos
- Visualización inline de imágenes en Odoo
- Adjuntos con peso 0 en Odoo
- Health check automático
- Manejo seguro de errores
- Almacenamiento organizado por modelo e ID

---

## 📁 Estructura de almacenamiento

/data/files/
├── res.partner/
│ └── 123/
│ ├── uuid_imagen.jpg
│ └── uuid_documento.pdf
└── project.task/
└── 456/


/data/files/
├── res.partner/
│ └── 123/
│ ├── uuid_imagen.jpg
│ └── uuid_documento.pdf
└── project.task/
└── 456/


---

## 🚀 File API (FastAPI)

### Health check

POST /upload
Headers:
  X-API-KEY: <TOKEN>

Form-data:
  files
  model
  record_id
  client_name (opcional)
  client_dni (opcional)


### Acceso a archivos

GET /files/{model}/{record_id}/{filename}

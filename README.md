# LinkedIn Scraper

Script de Python para extraer información de contacto de perfiles de LinkedIn mediante scraping con Playwright.

## Requisitos

- Python 3.8+
- Navegador Chromium (se instala con Playwright)

## Instalación

1. Clonar el repositorio y crear un entorno virtual:

```bash
python -m venv venv
```

2. Activar el entorno virtual:

- Windows:
```bash
venv\Scripts\activate
```

- Linux/Mac:
```bash
source venv/bin/activate
```

3. Instalar las dependencias:

```bash
pip install -r requirements.txt
```

4. Instalar los navegadores de Playwright:

```bash
playwright install chromium
```

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
# Usuario de LinkedIn a scrapear
LINKEDIN_USERNAME=pablojacomea
```

### Variables disponibles

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `LINKEDIN_USERNAME` | Nombre de usuario del perfil de LinkedIn a extraer | `pablojacomea` |

## Uso

Ejecutar el script:

```bash
python scraper_linkedin.py
```

El script:
1. Abrirá el navegador con LinkedIn
2. Esperará 60 segundos para que iniciés sesión manualmente
3. Navegará al perfil objetivo
4. Extraerá la información de contacto (email, teléfonos, websites)
5. Guardará los resultados en un archivo JSON

## Notas

- La sesión de LinkedIn se guarda en `linkedin_session.json` para no tener que iniciar sesión en cada ejecución
- El script requiere login manual ya que LinkedIn tiene protecciones contra automatización
- Respeta los Términos de Servicio de LinkedIn al usar este script

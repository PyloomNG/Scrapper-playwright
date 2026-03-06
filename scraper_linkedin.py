import asyncio
import json
import re
import os
from datetime import datetime
from playwright.async_api import async_playwright
from dotenv import load_dotenv

# Cargar variables de entorno desde .env (opcional, para otros usos)
load_dotenv()

# Usuario de LinkedIn a extraer
LINKEDIN_USERNAME = os.getenv("LINKEDIN_USERNAME", "pablojacomea")

print("="*70)
print("🔓 MODO MANUAL: Inicia sesión en LinkedIn y el script continuará")
print("="*70)
print(f"👤 Perfil objetivo: {LINKEDIN_USERNAME}")
print("="*70)

async def wait_for_manual_login(context, page, wait_seconds=60):
    """
    Abre la página de LinkedIn y espera a que el usuario inicie sesión manualmente.
    """
    print("\n🔐 Esperando login manual...")
    print(f"  🌐 Abriendo LinkedIn...")

    # Intentar cargar sesión guardada previamente
    session_file = 'linkedin_session.json'
    if os.path.exists(session_file):
        print("  📂 Cargando sesión guardada...")
        try:
            with open(session_file, 'r') as f:
                storage_state = json.load(f)

            # Cerrar contexto actual y crear uno nuevo con la sesión
            await context.close()
            context = await page.context.browser.new_context(
                viewport={'width': 1280, 'height': 720},
                storage_state=storage_state,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            await page.goto("https://www.linkedin.com/feed/", wait_until='networkidle')
            print("  ✅ Sesión cargada!")

            # Verificar si sigue logueado
            if "linkedin.com/feed" in page.url or "linkedin.com/in/" in page.url:
                print("  ✅ Sesión activa - continuando...")
                return context, page
            else:
                print("  ⚠️ Sesión expirada, necesitas login manual")
        except Exception as e:
            print(f"  ⚠️ No se pudo cargar sesión: {e}")

    # Si no hay sesión, abrir login manual
    await page.goto("https://www.linkedin.com/login", wait_until='networkidle')

    print(f"\n⏳ Tienes {wait_seconds} segundos para iniciar sesión manualmente.")
    print("  👀 El navegador está abierto - ¡inicia sesión ahora!")
    print("  ⏱️ El script continuará automáticamente en 1 minuto...")

    # Barra de progreso visual
    for i in range(wait_seconds):
        await asyncio.sleep(1)
        if (i + 1) % 10 == 0:
            print(f"  ⏱️ {wait_seconds - i - 1} segundos restantes...")

    # Verificar que el login fue exitoso
    if "linkedin.com/feed" in page.url or "linkedin.com/in/" in page.url:
        print("\n  ✅ Login detectado - Continuing con el scraping...")
    else:
        print(f"\n  ⚠️ URL actual: {page.url}")
        await page.screenshot(path='login_check.png')
        print("  ℹ️ Continuando de todos modos...")

    return context, page

async def extract_contact(profile_username):
    """
    Extrae contacto después de login manual
    """
    profile_url = f"https://www.linkedin.com/in/{profile_username}/?locale=en_US"
    print("="*70)
    print("🔍 EXTRACTOR DE CONTACTO - MODO MANUAL")
    print("="*70)
    print(f"📍 Perfil objetivo: {profile_url}")
    print("="*70)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--no-first-run',
                '--no-zygote',
                '--disable-gpu'
            ]
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 720},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        page = await context.new_page()

        # Ocultar webdriver
        await page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)
        
        contact_data = {
            'fecha_scrapeo': datetime.now().isoformat(),
            'perfil': profile_url,
            'nombre': None,
            'email_linkedin': None,
            'telefonos': [],
            'websites': [],
            'fecha_conexion': None,
            'estado': 'En proceso'
        }

        try:
            # PASO 1: ESPERAR LOGIN MANUAL
            context, page = await wait_for_manual_login(context, page, wait_seconds=60)

            # PASO 2: Guardar sesión para futuros usos
            print("\n💾 Guardando sesión para futuros usos...")
            storage = await context.storage_state()
            with open('linkedin_session.json', 'w') as f:
                json.dump(storage, f)
            print("  ✅ Sesión guardada en 'linkedin_session.json'")

            # PASO 3: Navegar al perfil
            print(f"\n🌐 Navegando al perfil {profile_username}...")
            await page.goto(profile_url, wait_until='domcontentloaded', timeout=30000)
            await asyncio.sleep(4)

            # PASO 4: Buscar Contact info
            print("\n🔗 Buscando 'Contact info'...")
            contact_link = None
            
            selectores = [
                "a[href*='overlay/contact-info']",
                "#top-card-text-details-contact-info",
                "a:has-text('Contact info')",
                "a:has-text('Información de contacto')"
            ]
            
            for selector in selectores:
                contact_link = await page.query_selector(selector)
                if contact_link:
                    print(f"  ✅ Encontrado con selector: {selector}")
                    await page.evaluate('(el) => el.style.border = "3px solid red"', contact_link)
                    await asyncio.sleep(1)
                    break
            
            if not contact_link:
                print("❌ No se encontró el enlace 'Contact info'")
                contact_data['estado'] = 'Enlace no encontrado'
                return contact_data
            
            # PASO 5: Hacer clic
            print("\n🖱️ Haciendo clic en el enlace...")
            await contact_link.click()
            print("  ✅ Clic realizado")
            
            print("\n⏳ Esperando a que cargue el modal de contacto...")
            await asyncio.sleep(5)
            
            # PASO 6: Extraer información
            print("\n📋 Extrayendo información...")
            
            # Email
            email_link = await page.query_selector("a[href^='mailto:']")
            if email_link:
                email_href = await email_link.get_attribute('href')
                if email_href:
                    contact_data['email_linkedin'] = email_href.replace('mailto:', '')
                    print(f"  ✅ Email encontrado: {contact_data['email_linkedin']}")
                    await page.evaluate('(el) => el.style.border = "3px solid green"', email_link)
            else:
                print("  ❌ No se encontró enlace mailto")
                
                # Buscar email específico
                page_text = await page.text_content('body')
                email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                emails = re.findall(email_pattern, page_text)
                valid_emails = [e for e in emails if 'example' not in e and 'linkedin.com' not in e]
                if valid_emails:
                    contact_data['email_linkedin'] = valid_emails[0]
                    print(f"  ✅ Email encontrado por regex: {contact_data['email_linkedin']}")
            
            # Nombre
            nombre_elem = await page.query_selector("h1#pv-contact-info")
            if not nombre_elem:
                nombre_elem = await page.query_selector("h1")
            if nombre_elem:
                contact_data['nombre'] = await nombre_elem.text_content()
                print(f"  👤 Nombre: {contact_data['nombre']}")
            
            # Fecha conexión
            fecha_elem = await page.query_selector("span.t-14.t-black.t-normal")
            if fecha_elem:
                contact_data['fecha_conexion'] = await fecha_elem.text_content()
                print(f"  📅 Conectado: {contact_data['fecha_conexion']}")
            
            # Teléfonos
            page_text = await page.text_content('body')
            phone_pattern = r'(\+\d{1,3}[\s-]?)?\(?\d{2,4}\)?[\s-]?\d{3,4}[\s-]?\d{3,4}'
            phones = re.findall(phone_pattern, page_text)
            contact_data['telefonos'] = list(set([''.join(p) for p in phones if p]))
            if contact_data['telefonos']:
                print(f"  📱 Teléfonos: {', '.join(contact_data['telefonos'])}")
            
            contact_data['estado'] = 'Completado'
            
            # PASO 7: Screenshot final
            screenshot_file = f"contacto_{profile_username}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await page.screenshot(path=screenshot_file)
            print(f"\n📸 Screenshot guardado: '{screenshot_file}'")

        except Exception as e:
            print(f"❌ Error durante la ejecución: {e}")
            await page.screenshot(path='error.png')
            contact_data['estado'] = f'Error: {str(e)[:50]}'

        finally:
            print("\n⏳ El navegador se cerrará en 15 segundos...")
            print("¡Revisa que todo esté correcto!")
            await asyncio.sleep(15)
            await browser.close()
            print("👋 Navegador cerrado.")

        return contact_data

def guardar_resultados(data, profile_username):
    """Guarda los datos en un archivo JSON"""
    if not data:
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"contacto_{profile_username}_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"💾 Datos guardados en: '{filename}'")

async def main():
    print("🚀 INICIANDO EXTRACCIÓN - MODO MANUAL")
    print("⏱️  El script abrirá LinkedIn y esperará 1 minuto para que inicies sesión")
    print("="*70)

    resultado = await extract_contact(LINKEDIN_USERNAME)

    if resultado:
        print("\n" + "="*70)
        print("📋 RESUMEN DE LA EXTRACCIÓN")
        print("="*70)
        print(f"Estado: {resultado['estado']}")
        print(f"Nombre: {resultado['nombre']}")
        print(f"Email en LinkedIn: {resultado['email_linkedin']}")
        print(f"Teléfonos: {', '.join(resultado['telefonos']) if resultado['telefonos'] else 'No encontrados'}")
        print(f"Conectado: {resultado['fecha_conexion']}")

        guardar_resultados(resultado, LINKEDIN_USERNAME)

        print("\n✨ PROCESO COMPLETADO")

if __name__ == "__main__":
    asyncio.run(main())
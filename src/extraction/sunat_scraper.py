import random
import time
from playwright.sync_api import Playwright


def sunat_consultation(playwright: Playwright, valor: str) -> dict | None:

    browser = playwright.chromium.launch(headless=True)

    context = browser.new_context(
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        viewport={"width": 1366, "height": 768},
    )

    page = context.new_page()

    try:

        print(f"Se está realizando la consulta: {valor} ...")

        page.goto("https://e-consultaruc.sunat.gob.pe/", wait_until="networkidle")

        page.wait_for_selector("#btnPorRuc", timeout=10000)

        page.locator("#btnPorRuc").click()

        page.locator("#txtRuc").press_sequentially(valor, delay=random.randint(80, 150))

        time.sleep(random.uniform(1.0, 2.5))

        page.locator("#btnAceptar").click()

        page.wait_for_timeout(3000)

        text = page.locator("body").inner_text()

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        data = {}

        for i, line in enumerate(lines):

            if line == "Número de RUC:":

                ruc, razon_social = lines[i + 1].split(" - ", 1)

                data["ruc"] = ruc
                data["razon_social"] = razon_social

            elif line == "Tipo Contribuyente:":

                data["tipo_contribuyente"] = lines[i + 1]

            elif line == "Nombre Comercial:":

                data["nombre_comercial"] = lines[i + 1]

            elif line == "Fecha de Inscripción:":

                data["fecha_inscripcion"] = lines[i + 1]

            elif line == "Fecha de Inicio de Actividades:":

                data["fecha_inicio_actividades"] = lines[i + 1]

            elif line == "Estado del Contribuyente:":

                data["estado_contribuyente"] = lines[i + 1]

            elif line == "Condición del Contribuyente:":

                data["condicion_contribuyente"] = lines[i + 1]

            elif line == "Domicilio Fiscal:":

                data["domicilio_fiscal"] = lines[i + 1]

            elif line == "Actividad Comercio Exterior:":

                data["actividad_comercio_exterior"] = lines[i + 1]

            elif line == "Sistema Contabilidad:":

                data["sistema_contabilidad"] = lines[i + 1]

            elif line == "Actividad(es) Económica(s):":

                j = i + 1

                while j < len(lines) and not lines[j].endswith(":"):

                    if lines[j].startswith("Principal"):

                        data["actividad_principal"] = lines[j]

                    elif lines[j].startswith("Secundaria"):

                        data.setdefault("actividades_secundarias", []).append(lines[j])

                    j += 1

        print(f"Consulta exitosa para el RUC: {valor}")

        page.locator(".btn.btn-primary.btn-sm.btnInfDeuCoa").click()
        page.wait_for_timeout(3000)

        text = page.locator("body").inner_text()

        lines = [line.strip() for line in text.split("\n") if line.strip()]

        data_deuda_coactiva = {
            "ruc": valor,
            "tiene_deuda_coactiva": False,
            "deudas": [],
        }

        for line in lines:
            if "DEUDA COACTIVA REMITIDA A CENTRALES DE RIESGO DE" in line:
                info_contribuyente = line.replace(
                    "DEUDA COACTIVA REMITIDA A CENTRALES DE RIESGO DE ", ""
                )
                ruc, razon_social = info_contribuyente.split(" - ", 1)
                data_deuda_coactiva["ruc"] = ruc.strip()
                break

        if (
            "No se ha remitido deuda en cobranza coactiva que corresponda al contribuyente consultado."
            in lines
        ):
            data_deuda_coactiva["tiene_deuda_coactiva"] = False

        elif (
            "Monto de la Deuda\tPeríodo Tributario\tFecha de Inicio de Cobranza Coactiva\tEntidad Asociada a la Deuda"
            in lines
        ):
            data_deuda_coactiva["tiene_deuda_coactiva"] = True

            indice_cabecera = lines.index(
                "Monto de la Deuda\tPeríodo Tributario\tFecha de Inicio de Cobranza Coactiva\tEntidad Asociada a la Deuda"
            )

            for line in lines[indice_cabecera + 1 :]:
                if "\t" not in line:
                    break

                campos = line.split("\t")

                deuda_info = {
                    "ruc": data_deuda_coactiva["ruc"],
                    "tiene_deuda": "SI",
                    "monto": float(campos[0]),
                    "periodo": campos[1].strip(),
                    "fecha_inicio": campos[2].strip(),
                    "entidad": campos[3].strip(),
                }
                data_deuda_coactiva["deudas"].append(deuda_info)

        if not data_deuda_coactiva["deudas"]:
            deuda_vacia = {
                "ruc": data_deuda_coactiva["ruc"],
                "tiene_deuda": "NO",
                "monto": "-",
                "periodo": "-",
                "fecha_inicio": "-",
                "entidad": "-",
            }
            data_deuda_coactiva["deudas"].append(deuda_vacia)

        return data, data_deuda_coactiva["deudas"]

    except Exception as e:

        print(f"Error durante la consulta {valor}: {e}")

        return None

    finally:

        context.close()
        browser.close()

#!/usr/bin/env python3
"""Actualización diaria del comparador de luz.

1) Descarga el PVPC (precio horario de la tarifa regulada) de la API pública de
   Red Eléctrica (REData) y guarda el histórico diario.
2) Comprueba que los precios que tenemos de cada compañía siguen apareciendo en
   las páginas que usamos como fuente. NO cambia los precios solo: avisa.
3) Genera data/data.json, que es lo que lee la app (index.html).

Solo usa la librería estándar de Python. Uso:
    python scripts/update.py            # actualización completa
    python scripts/update.py --offline  # solo regenera data.json con lo que hay
"""
import json, os, sys, time, datetime as dt
import urllib.request, urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
UA = "comparador-luz/1.0 (proyecto personal; una consulta al día)"
API = "https://apidatos.ree.es/es/datos/mercados/precios-mercados-tiempo-real"
DIAS_ATRAS = 10      # cuántos días se vuelven a pedir cada noche
MAX_HISTORIA = 90    # días que se conservan


def cargar(nombre, defecto):
    ruta = os.path.join(DATA, nombre)
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8") as f:
            return json.load(f)
    return defecto


def guardar(nombre, obj):
    with open(os.path.join(DATA, nombre), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def descargar(url, intentos=3, timeout=30):
    ultimo = None
    for i in range(intentos):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read().decode("utf-8", "replace")
        except Exception as e:  # noqa: BLE001
            ultimo = e
            time.sleep(2 * (i + 1))
    raise RuntimeError(str(ultimo))


# ---------- PVPC ----------
def parse_pvpc(payload):
    """Del JSON de REData devuelve [(fecha_hora, €/kWh)] del PVPC (la API da €/MWh)."""
    for item in payload.get("included", []):
        if str(item.get("type", "")).upper() == "PVPC":
            vals = item["attributes"]["values"]
            return [(v["datetime"], float(v["value"]) / 1000.0) for v in vals]
    return []


def resumen_dia(dia, vals):
    """Resumen del día; None si está incompleto (menos de 23 horas)."""
    if len(vals) < 23:
        return None
    precios = [p for _, p in vals]
    imin = precios.index(min(precios))
    imax = precios.index(max(precios))
    return {
        "d": dia,
        "avg": round(sum(precios) / len(precios), 4),
        "min": round(precios[imin], 4), "min_h": int(vals[imin][0][11:13]),
        "max": round(precios[imax], 4), "max_h": int(vals[imax][0][11:13]),
        "horas": [round(p, 4) for p in precios],
        "fuente": "REData (Red Eléctrica)",
    }


def actualizar_pvpc(historia):
    por_dia = {h["d"]: h for h in historia}
    hoy = dt.date.today()
    for n in range(-DIAS_ATRAS, 2):          # hasta mañana (se publica ~20:30)
        dia = (hoy + dt.timedelta(days=n)).isoformat()
        q = urllib.parse.urlencode({
            "start_date": dia + "T00:00", "end_date": dia + "T23:59", "time_trunc": "hour"})
        try:
            res = resumen_dia(dia, parse_pvpc(json.loads(descargar(API + "?" + q))))
        except Exception as e:  # noqa: BLE001
            print(f"PVPC {dia}: error ({e})")
            continue
        if res:
            por_dia[dia] = res
            print(f"PVPC {dia}: media {res['avg']} €/kWh")
        else:
            print(f"PVPC {dia}: sin datos completos")
        time.sleep(1)
    return [por_dia[d] for d in sorted(por_dia)][-MAX_HISTORIA:]


# ---------- Comprobación de precios de compañías ----------
def encuentra(html, termino):
    """Busca un precio tanto con coma (0,1659) como con punto (0.1659)."""
    h = html.replace("\xa0", " ")
    return termino in h or termino.replace(",", ".") in h


def comprobar_pagina(html, buscar):
    return [t for t in buscar if not encuentra(html, t)]


def comprobar_companias(companias):
    resultado, ahora = {}, dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes")
    for c in companias:
        estado, detalle = "error", []
        for fuente in c.get("comprobar", []):
            try:
                faltan = comprobar_pagina(descargar(fuente["url"]), fuente["buscar"])
            except Exception as e:  # noqa: BLE001
                detalle.append({"url": fuente["url"], "error": str(e)[:120]})
                continue
            detalle.append({"url": fuente["url"], "faltan": faltan})
            if not faltan:
                estado = "ok"
                break
            estado = "cambio"
            time.sleep(1)
        resultado[c["n"]] = {"estado": estado, "fecha": ahora, "detalle": detalle}
        print(f"{c['n']}: {estado}")
    return resultado


# ---------- Salida para la app ----------
def generar(companias, historia, comprobaciones):
    salida = {
        "generado": dt.datetime.now(dt.timezone.utc).isoformat(timespec="minutes"),
        "pvpc": {"dias": [{k: v for k, v in h.items() if k != "horas"} for h in historia]},
        "comprobaciones": {n: {"estado": v["estado"], "fecha": v["fecha"]}
                           for n, v in comprobaciones.items()},
        "companias": [{k: v for k, v in c.items() if k != "comprobar"} for c in companias],
    }
    guardar("data.json", salida)


def main():
    offline = "--offline" in sys.argv
    companias = cargar("companies.json", [])
    historia = cargar("pvpc_history.json", [])
    comprobaciones = cargar("checks.json", {})
    if not offline:
        historia = actualizar_pvpc(historia)
        guardar("pvpc_history.json", historia)
        comprobaciones = comprobar_companias(companias)
        guardar("checks.json", comprobaciones)
    generar(companias, historia, comprobaciones)
    print("data/data.json generado")


if __name__ == "__main__":
    main()

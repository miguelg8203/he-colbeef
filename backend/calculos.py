"""
calculos.py - Lógica exacta del Excel HE Colbeef
Fórmulas traducidas directamente del Excel original.
Columnas: B=esFestivo, E=fecha, F=entrada, G=salida, H=descanso(horas)
DIASEM(E,2): 1=Lun, 2=Mar, 3=Mie, 4=Jue, 5=Vie, 6=Sab, 7=Dom
"""
from datetime import date, timedelta
from typing import List, Dict, Any


def to_min(t: str) -> int:
    if not t: return 0
    h, m = t.split(":")
    return int(h)*60 + int(m)

def to_dec(t: str) -> float:
    """Hora a decimal de día (como Excel). 06:00 = 0.25"""
    if not t: return 0.0
    return to_min(t) / 1440.0

def get_lunes(f: date) -> date:
    return f - timedelta(days=f.weekday())

def add_day(f: date, n: int = 1) -> date:
    return f + timedelta(days=n)

def es_descanso_culto_semana(regs):
    for f, r in regs.items():
        dow = f.weekday() if hasattr(f,'weekday') else date.fromisoformat(str(f)).weekday()
        if dow == 5 and (r.get("observacion") or "") == "DESCANSO POR CULTO":
            return True
    return False

def diasem(f: date) -> int:
    """DIASEM(f, 2): 1=Lun ... 6=Sab, 7=Dom"""
    return f.weekday() + 1  # weekday(): 0=Lun...6=Dom → +1 = 1=Lun...7=Dom

# Constantes horarias en decimal de día
H = {
    "00:00": 0.0,
    "02:00": 2/24,
    "06:00": 6/24,
    "07:00": 7/24,
    "14:00": 14/24,
    "19:00": 19/24,
    "22:00": 22/24,
    "30:00": 30/24,  # 06:00 del día siguiente
}

def hn(t: str) -> float:
    """HORANUMERO en decimal"""
    return to_min(t) / 1440.0


def calcular_fila(fecha: date, registro: dict, obs_map: dict, registros_todos: dict = None) -> dict:
    """
    Calcula HED, HEN, RNO, HEFD, HEFN, RFD, RFN para una fila.
    Traducción directa de las fórmulas Excel.
    """
    res = dict(horas_trab=0.0, hed=0.0, hen=0.0, rno=0.0,
               hefd=0.0, hefn=0.0, rfd=0.0, rfn=0.0, min_dia=0.0)

    entrada_s = registro.get("entrada", "")
    salida_s  = registro.get("salida", "")
    obs       = (registro.get("observacion") or "").strip().upper()
    es_fest   = registro.get("es_festivo", False)
    des_raw   = registro.get("descanso") or 0
    # descanso puede venir en minutos (>3) o en horas (<3)
    des_h     = des_raw / 60.0 if des_raw > 3 else float(des_raw)

    # Sin horario: observación con horas fijas
    if not entrada_s or not salida_s:
        if obs and obs in obs_map:
            ob = obs_map[obs]
            if ob["cuenta_ot"] and ob["horas_fijas"] > 0:
                res["horas_trab"] = ob["horas_fijas"]
                res["min_dia"]    = ob["horas_fijas"] * 60
        return res

    F = to_dec(entrada_s)   # entrada en decimal
    G = to_dec(salida_s)    # salida en decimal
    dw = diasem(fecha)      # 1=Lun...6=Sab, 7=Dom
    B  = es_fest

    # Si salida < entrada, cruza medianoche → G+1
    G_adj = G + 1 if G < F else G

    # Horas trabajadas
    trab_h = (G_adj - F) * 24 - des_h
    if trab_h <= 0:
        return res
    res["horas_trab"] = round(trab_h, 2)
    res["min_dia"]    = round(trab_h * 60)

    # ── HED ──────────────────────────────────────────────────────────────────
    # Traduccion exacta formula Excel
    if not B and entrada_s and salida_s:
        if dw == 7:  # Domingo → no HED
            hed = 0.0
        elif dw == 6:  # Sábado
            if F == hn("06:00"):
                hed = (min(G_adj, hn("19:00")) - F) * 24 - 4 - des_h
            elif F == hn("14:00"):
                hed = 1.0
            elif F == hn("07:00"):
                hed = max(0, (min(G_adj, hn("19:00")) - F) * 24 - 8 - des_h)
            else:
                hed = 0.0
        elif F == hn("22:00"):
            hed = max(0, (G - hn("06:00")) * 24 - des_h) if G > hn("06:00") else 0.0
        elif F == hn("07:00"):
            hed = max(0, (min(G_adj, hn("19:00")) - F) * 24 - 8 - des_h)
        elif F < hn("14:00"):
            # Formula Excel: (MIN(G,19:00) - 14:00)*24 - descanso
            g_cap = min(G_adj, hn("19:00"))
            if g_cap <= hn("06:00"):
                g_cap += 1
            hed = max(0, (g_cap - hn("14:00")) * 24 - des_h)
        else:
            hed = 0.0
        res["hed"] = round(max(0, hed), 1)

    # ── HEN ──────────────────────────────────────────────────────────────────
    if not B and entrada_s and salida_s:
        if F == hn("06:00") and G_adj > hn("19:00"):
            hen = (G_adj - hn("19:00")) * 24
        elif dw == 6 and F == hn("22:00") and G == hn("06:00"):
            hen = 0.0
        elif dw == 6:
            if hn("14:00") <= F < hn("22:00"):
                hen = max(0, (min(G_adj, hn("22:00")) - hn("19:00")) * 24)
            else:
                hen = 0.0
        elif dw == 5 and F >= hn("22:00"):
            v = (G_adj - hn("30:00")) * 24
            hen = 0.0 if v >= 24 else max(0, v)
        elif hn("14:00") <= F < hn("22:00"):
            # Formula Excel: MAX(0,(MIN(G_adj,22:00)-22:00)*24)
            hen = max(0, (min(G_adj, hn("22:00")) - hn("22:00")) * 24)
        else:
            hen = 0.0
        res["hen"] = round(max(0, hen), 1)

    # ── RNO ──────────────────────────────────────────────────────────────────
    if entrada_s and salida_s:
        if dw == 5 and F == hn("22:00"):
            # Formula Excel: verifica si domingo (E+2) tambien tiene F=22:00
            # Si no tenemos esa info, usamos el calculo completo
            dom_fecha = fecha + timedelta(days=2)
            reg_dom = (registros_todos or {}).get(dom_fecha, {})
            if not reg_dom and registros_todos:
                # Try string key
                reg_dom = registros_todos.get(dom_fecha.isoformat(), {})
            dom_entrada = reg_dom.get("entrada", "")
            if dom_entrada and to_dec(dom_entrada) == hn("22:00"):
                rno = 4.0  # Domingo tambien es noche → RNO=4
            else:
                rno = max(0, (min(G_adj, hn("06:00")+1) - hn("22:00")) * 24)
        elif dw == 6 and F == hn("22:00"):
            rno = max(0, (min(G_adj, 1.0) - hn("22:00")) * 24)
        elif dw == 6:
            rno = 0.0
        elif dw == 7 and F == hn("22:00"):
            rno = 0.0  # Domingo noche → todo HEFN
        elif dw == 7:
            rno = 0.0
        elif B:
            if F >= hn("22:00"):
                rno = max(0, (min(G_adj, hn("06:00") + 1) - 1) * 24)
            else:
                rno = 0.0
        elif F < hn("14:00"):
            rno = 0.0
        elif hn("14:00") <= F < hn("22:00"):
            rno = max(0, (min(G_adj, hn("22:00")) - hn("19:00")) * 24)
        else:
            rno = max(0, (min(G_adj, hn("06:00") + 1) - hn("22:00")) * 24)
        res["rno"] = round(max(0, rno), 1)

    # ── HEFD ─────────────────────────────────────────────────────────────────
    if entrada_s and salida_s:
        if dw == 7:  # Domingo
            if F < hn("14:00"):
                hefd = max(0, round((min(G_adj, hn("19:00")) - F) * 24 - des_h, 2))
            elif hn("14:00") <= F < hn("22:00"):
                hefd = max(0, round((min(G_adj, hn("19:00")) - F) * 24 - des_h, 2))
            else:
                hefd = 0.0
        elif B:
            if F == hn("22:00"):
                hefd = max(0, round((G_adj - hn("06:00")) * 24 - des_h, 2))
            else:
                hefd = max(0, round((min(G_adj, hn("19:00")) - (F + 8/24)) * 24 - des_h, 2))
        else:
            hefd = 0.0
        res["hefd"] = round(max(0, hefd), 1)

    # ── HEFN ─────────────────────────────────────────────────────────────────
    if entrada_s and salida_s:
        if dw == 6 and F == hn("22:00"):
            hefn = max(0, (G_adj - hn("02:00") - 1) * 24)
        elif dw == 7:
            if F >= hn("22:00"):
                hefn = (G_adj - F) * 24  # Dom noche → todo HEFN
            else:
                hefn = max(0, (G_adj - hn("19:00")) * 24)
        elif B and (G_adj - F) * 24 > 8:
            if F == hn("22:00"):
                hefn = 0.0
            elif F == hn("14:00"):
                hefn = max(0, (min(G_adj, 1.0) - hn("22:00")) * 24)
            else:
                hefn = max(0, (G_adj - hn("19:00")) * 24)
        else:
            hefn = 0.0
        res["hefn"] = round(max(0, hefn), 1)

    # ── RFD ──────────────────────────────────────────────────────────────────
    if entrada_s and salida_s and B:
        if F < hn("14:00"):
            rfd = min(8, max(0, (min(G_adj, hn("19:00")) - F) * 24))
        elif hn("14:00") <= F < hn("22:00"):
            rfd = min(8, max(0, (min(G_adj, hn("19:00")) - hn("14:00")) * 24))
        else:
            rfd = 0.0
        res["rfd"] = round(max(0, rfd), 1)

    # ── RFN ──────────────────────────────────────────────────────────────────
    if entrada_s and salida_s:
        if dw == 6 and F == hn("22:00"):
            rfn = max(0, (min(G_adj, hn("02:00") + 1) - 1) * 24)
        elif dw == 7 and F >= hn("22:00"):
            rfn = 0.0  # Domingo noche → todo HEFN
        elif B:
            if hn("14:00") <= F < hn("22:00"):
                rfn = max(0, (min(G_adj, hn("22:00")) - hn("19:00")) * 24)
            elif F >= hn("22:00"):
                rfn = max(0, (min(G_adj + 1, 1.0) - hn("22:00")) * 24)
            else:
                rfn = 0.0
        else:
            rfn = 0.0
        res["rfn"] = round(max(0, rfn), 1)

    return res


# ── Semana y Periodo ──────────────────────────────────────────────────────────

def clasificar_dia(fecha, registro, min_acum_semana, cfg, es_culto, obs_map,
                   registros_todos=None):
    """Wrapper para compatibilidad con el resto del código."""
    obs_map_simple = obs_map
    return calcular_fila(fecha, registro, obs_map_simple)


def calcular_semana(dias, registros, cfg, obs_map):
    es_culto = es_descanso_culto_semana({f: registros.get(f,{}) for f in dias})
    min_acum = 0.0
    rows = []
    for fecha in dias:
        reg = registros.get(fecha, {})
        res = calcular_fila(fecha, reg, obs_map, registros_todos=registros)
        rows.append({"fecha": fecha, "resultado": res, "registro": reg})
        min_acum += res["min_dia"]
    return {"rows": rows,
            "ot_semana":    round(min_acum/60 - cfg["horas_sem"], 1),
            "horas_semana": round(min_acum/60, 1)}


def calcular_periodo(year, month, registros, cfg, obs_map):
    inicio  = date(year, month, 21)
    mes_fin = month+1 if month<12 else 1
    año_fin = year if month<12 else year+1
    fin     = date(año_fin, mes_fin, 20)

    dias = []
    d = inicio
    while d <= fin:
        dias.append(d)
        d += timedelta(days=1)

    # Agrupar Dom→Sáb
    semanas = {}
    for d in dias:
        dow = d.weekday()
        dom = d if dow == 6 else d - timedelta(days=dow+1)
        if dom not in semanas:
            semanas[dom] = []
        semanas[dom].append(d)

    semanas_result = []
    for dom in sorted(semanas.keys()):
        res = calcular_semana(semanas[dom], registros, cfg, obs_map)
        semanas_result.append({"lunes": dom, **res})

    sub = dict(hed=0.0, hen=0.0, rno=0.0, hefd=0.0, hefn=0.0,
               rfd=0.0, rfn=0.0, horas_total=0.0, ot_total=0.0)
    for sem in semanas_result:
        sub["ot_total"]    += sem["ot_semana"]
        sub["horas_total"] += sem["horas_semana"]
        for row in sem["rows"]:
            for col in ["hed","hen","rno","hefd","hefn","rfd","rfn"]:
                sub[col] += row["resultado"][col]
    for k in sub:
        sub[k] = round(sub[k], 1)

    return {"semanas": semanas_result, "subtotales": sub,
            "dias": [d.isoformat() for d in dias],
            "inicio": inicio.isoformat(), "fin": fin.isoformat()}


FACTORES = {"hed":1.25,"hen":1.75,"rno":0.35,
            "hefd":2.05,"hefn":2.55,"rfd":0.80,"rfn":1.15}

def calcular_valores(sueldo, horas_sem, subtotales):
    # Formula Excel: Sueldo / jornada_mensual * horas * factor
    jornada_mensual = round((horas_sem / 6) * 30)  # 220 para 44h, 210 para 42h
    vh = sueldo / jornada_mensual
    res = {}; neto = 0.0
    for col, f in FACTORES.items():
        v = round(subtotales.get(col,0.0)*vh*f, 2)
        res[f"val_{col}"] = v; neto += v
    res["neto"] = round(neto,2); res["valor_hora"] = round(vh,2)
    return res

"""
calculos.py
Lógica de clasificación de horas extras según Ley 2101/2021
Colombia: diurno 06:00-19:00, nocturno 19:00-06:00
Jornada: 44h semanales (6 días)
"""
from datetime import date, timedelta
from typing import List, Dict, Any


# ── Utilidades de tiempo ──────────────────────────────────────────────────────

def to_min(t: str) -> int:
    if not t: return 0
    h, m = t.split(":")
    return int(h) * 60 + int(m)


def overlap(a1: int, a2: int, b1: int, b2: int) -> int:
    return max(0, min(a2, b2) - max(a1, b1))


def split_dn(inicio: int, fin: int, ds: int, de: int):
    """
    Divide [inicio, fin) en minutos diurnos y nocturnos.
    fin puede ser >= 1440 si cruza medianoche.
    ds = inicio diurno (ej. 360), de = fin diurno (ej. 1140)
    Nocturno = [0, ds) + [de, 1440)
    """
    fin_hoy = min(fin, 1440)
    diurno  = overlap(inicio, fin_hoy, ds, de)
    noct    = overlap(inicio, fin_hoy, 0, ds) + overlap(inicio, fin_hoy, de, 1440)

    if fin > 1440:
        fin2    = fin - 1440
        diurno += overlap(0, fin2, ds, de)
        noct   += overlap(0, fin2, 0, ds) + overlap(0, fin2, de, 1440)

    return diurno, noct


# ── Helpers de fecha ──────────────────────────────────────────────────────────

def get_lunes(f: date) -> date:
    return f - timedelta(days=f.weekday())


def add_day(f: date, n: int = 1) -> date:
    return f + timedelta(days=n)


def es_descanso_culto_semana(registros_semana: Dict) -> bool:
    for f, r in registros_semana.items():
        if hasattr(f, 'weekday'):
            dow = f.weekday()
        else:
            dow = date.fromisoformat(str(f)).weekday()
        if dow == 5 and (r.get("observacion") or "") == "DESCANSO POR CULTO":
            return True
    return False


def dia_es_festivo(fecha: date, registros: Dict, es_culto: bool) -> bool:
    """
    Determina si una fecha es festivo/domingo para efectos de clasificación.
    - Domingo siempre es festivo (salvo técnico descanso por culto)
    - Cualquier día con checkbox es_festivo=True
    """
    dow = fecha.weekday()  # 0=lun … 6=dom
    es_dom = dow == 6
    reg = registros.get(fecha, {})
    es_fest_cb = reg.get("es_festivo", False)
    return es_fest_cb or (es_dom and not es_culto)


# ── Clasificar un segmento ────────────────────────────────────────────────────

def _clasificar_segmento(
    seg_s: int, seg_e: int, seg_des: int,
    seg_fest: bool,
    min_rest_jornada: float,
    ds: int, de: int,
    resultado: dict,
) -> float:
    """
    Clasifica un segmento horario y actualiza resultado.
    Retorna los minutos consumidos de jornada en este segmento.
    """
    seg_bruto = seg_e - seg_s
    seg_trab  = max(0, seg_bruto - seg_des)
    if seg_trab <= 0:
        return 0.0

    diurno_raw, noct_raw = split_dn(seg_s, seg_e, ds, de)
    ratio      = seg_trab / seg_bruto if seg_bruto > 0 else 0
    diurno_min = round(diurno_raw * ratio)
    noct_min   = round(noct_raw   * ratio)

    dentro = min(seg_trab, min_rest_jornada)
    exceso = seg_trab - dentro

    d_r = diurno_min / seg_trab if seg_trab > 0 else 0
    n_r = noct_min   / seg_trab if seg_trab > 0 else 0

    d_dentro = round(dentro * d_r)
    n_dentro = round(dentro * n_r)
    d_exceso = round(exceso * d_r)
    n_exceso = round(exceso * n_r)

    if seg_fest:
        resultado["rfd"]  += d_dentro / 60
        resultado["rfn"]  += n_dentro / 60
        resultado["hefd"] += d_exceso / 60
        resultado["hefn"] += n_exceso / 60
    else:
        resultado["rno"]  += n_dentro / 60
        resultado["hed"]  += d_exceso / 60
        resultado["hen"]  += n_exceso / 60

    return float(dentro)


# ── Clasificación de un día ───────────────────────────────────────────────────

def clasificar_dia(
    fecha: date,
    registro: dict,
    min_acum_semana: float,
    cfg: dict,
    es_culto: bool,
    obs_map: Dict[str, dict],
    registros_todos: Dict = None,   # ← todos los registros del periodo para consultar día siguiente
) -> dict:

    resultado = dict(horas_trab=0.0, hed=0.0, hen=0.0, rno=0.0,
                     hefd=0.0, hefn=0.0, rfd=0.0, rfn=0.0, min_dia=0.0)

    jornada_sem_min = cfg["horas_sem"] * 60
    ds = to_min(cfg["inicio_diurno"])
    de = to_min(cfg["fin_diurno"])

    # ── Festivo del día de inicio ─────────────────────────────────────────────
    regs = registros_todos or {fecha: registro}
    dia_fest_inicio = dia_es_festivo(fecha, {fecha: registro, **regs}, es_culto)

    obs_nombre = (registro.get("observacion") or "").strip().upper()
    entrada    = registro.get("entrada", "")
    salida     = registro.get("salida", "")

    # ── Sin horario: observación con horas fijas ──────────────────────────────
    if not entrada or not salida:
        if obs_nombre and obs_nombre in obs_map:
            ob = obs_map[obs_nombre]
            if ob["cuenta_ot"] and ob["horas_fijas"] > 0:
                min_obs = ob["horas_fijas"] * 60
                resultado["horas_trab"] = ob["horas_fijas"]
                resultado["min_dia"]    = min_obs
        return resultado

    # ── Tiempo bruto ──────────────────────────────────────────────────────────
    s = to_min(entrada)
    e = to_min(salida)
    if e <= s:
        e += 1440   # cruza medianoche

    des_min  = registro.get("descanso", 0) or 0
    trab_min = max(0, (e - s) - des_min)
    if trab_min <= 0:
        return resultado

    resultado["horas_trab"] = round(trab_min / 60, 2)
    resultado["min_dia"]    = trab_min

    # ── Partir en segmentos si cruza medianoche ───────────────────────────────
    min_rest = max(0.0, jornada_sem_min - min_acum_semana)

    if e > 1440:
        raw1 = 1440 - s
        raw2 = e - 1440
        raw_tot = e - s
        des1 = round(des_min * raw1 / raw_tot)
        des2 = des_min - des1

        # Día siguiente: ¿es festivo?
        fecha2     = add_day(fecha)
        dia_fest2  = dia_es_festivo(fecha2, regs, es_culto)

        # Segmento 1: día inicio (s → 1440)
        consumido = _clasificar_segmento(s, 1440, des1, dia_fest_inicio, min_rest, ds, de, resultado)
        min_rest  = max(0.0, min_rest - consumido)

        # Segmento 2: día siguiente (0 → raw2)
        _clasificar_segmento(0, raw2, des2, dia_fest2, min_rest, ds, de, resultado)
    else:
        _clasificar_segmento(s, e, des_min, dia_fest_inicio, min_rest, ds, de, resultado)

    for k in ["hed","hen","rno","hefd","hefn","rfd","rfn","horas_trab"]:
        resultado[k] = round(resultado[k], 1)

    return resultado


# ── Calcular semana ───────────────────────────────────────────────────────────

def calcular_semana(
    dias: List[date],
    registros: Dict[date, dict],
    cfg: dict,
    obs_map: Dict[str, dict],
) -> Dict[str, Any]:

    es_culto = es_descanso_culto_semana({f: registros.get(f, {}) for f in dias})
    min_acum = 0.0
    rows = []

    for fecha in dias:
        reg = registros.get(fecha, {})
        resultado = clasificar_dia(
            fecha, reg, min_acum, cfg, es_culto, obs_map,
            registros_todos=registros   # pasar todos para consultar día siguiente
        )
        rows.append({"fecha": fecha, "resultado": resultado, "registro": reg})
        min_acum += resultado["min_dia"]

    horas_sem = round(min_acum / 60, 1)
    ot_semana = round(horas_sem - cfg["horas_sem"], 1)

    return {"rows": rows, "ot_semana": ot_semana, "horas_semana": horas_sem}


# ── Calcular periodo ──────────────────────────────────────────────────────────

def calcular_periodo(
    year: int,
    month: int,
    registros: Dict[date, dict],
    cfg: dict,
    obs_map: Dict[str, dict],
) -> Dict[str, Any]:

    inicio  = date(year, month, 21)
    mes_fin = month + 1 if month < 12 else 1
    año_fin = year if month < 12 else year + 1
    fin     = date(año_fin, mes_fin, 20)

    dias_periodo = []
    d = inicio
    while d <= fin:
        dias_periodo.append(d)
        d += timedelta(days=1)

    # Agrupar por semana laboral Dom-Sáb
    # Semana empieza el domingo y termina el sábado
    semanas: Dict[date, List[date]] = {}
    for d in dias_periodo:
        dow = d.weekday()  # 0=lun … 6=dom
        if dow == 6:
            # Domingo es el INICIO de la semana
            dom = d
        else:
            # Para lun(0)→sáb(5) retroceder al domingo anterior
            dom = d - timedelta(days=dow + 1)
        if dom not in semanas:
            semanas[dom] = []
        semanas[dom].append(d)

    semanas_result = []
    for lun in sorted(semanas.keys()):
        res = calcular_semana(semanas[lun], registros, cfg, obs_map)
        semanas_result.append({"lunes": lun, **res})

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

    return {
        "semanas": semanas_result,
        "subtotales": sub,
        "dias": [d.isoformat() for d in dias_periodo],
        "inicio": inicio.isoformat(),
        "fin":    fin.isoformat(),
    }


# ── Factores y valores en pesos ───────────────────────────────────────────────

FACTORES = {
    "hed":  1.25,
    "hen":  1.75,
    "rno":  0.35,
    "hefd": 2.00,
    "hefn": 2.50,
    "rfd":  0.75,
    "rfn":  1.10,
}


def calcular_valores(sueldo: float, horas_sem: float, subtotales: dict) -> dict:
    valor_hora = sueldo / (horas_sem * 4.333333)
    resultado  = {}
    neto       = 0.0
    for col, factor in FACTORES.items():
        horas = subtotales.get(col, 0.0)
        valor = round(horas * valor_hora * factor, 2)
        resultado[f"val_{col}"] = valor
        neto += valor
    resultado["neto"]       = round(neto, 2)
    resultado["valor_hora"] = round(valor_hora, 2)
    return resultado

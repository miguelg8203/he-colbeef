"""
calculos.py - Lógica exacta del Excel HE Colbeef
Reforma Ley 2101 aplicada desde el 15 de julio de 2026
Nuevas categorías: HRFD (Recargo Festivo Diurno) y HRFN (Recargo Festivo Nocturno)
"""
import math
from datetime import date, timedelta

REFORMA     = date(2026, 7, 15)  # Jornada 7h + nuevas reglas HE
REFORMA_RFD = date(2026, 7,  1)  # RFD cambia a 0.90

def to_min(t):
    if not t: return 0
    h, m = t.split(":"); return int(h)*60+int(m)

def to_dec(t):
    if not t: return 0.0
    h, m = t.split(":"); return (int(h)*60+int(m))/1440.0

def get_lunes(f): return f-timedelta(days=f.weekday())
def add_day(f,n=1): return f+timedelta(days=n)

def es_descanso_culto_semana(regs):
    for f,r in regs.items():
        dow=f.weekday() if hasattr(f,"weekday") else date.fromisoformat(str(f)).weekday()
        if dow==5 and (r.get("observacion") or "")=="DESCANSO POR CULTO": return True
    return False

def diasem(f): return f.weekday()+1
def hn(t): return to_min(t)/1440.0


def _check_sig_fest(fecha, registros_todos):
    """Verifica si el día siguiente es festivo."""
    if not registros_todos: return False
    sig = fecha + timedelta(days=1)
    r = registros_todos.get(sig, {}) or registros_todos.get(sig.isoformat(), {})
    if isinstance(r, list): r = r[0] if r else {}
    return bool(r.get("es_festivo", False))


def _check_culto(fecha, registros_todos):
    """Verifica si el sábado de la semana tiene DESCANSO POR CULTO."""
    if not registros_todos: return False
    dow = fecha.weekday()
    dias_hasta_sab = 5 - dow if dow <= 5 else -1
    sab = fecha + timedelta(days=dias_hasta_sab) if dias_hasta_sab >= 0 else fecha - timedelta(days=1)
    r = registros_todos.get(sab, {}) or registros_todos.get(sab.isoformat(), {})
    if isinstance(r, list): r = r[0] if r else {}
    return (r.get("observacion") or "").strip().upper() == "DESCANSO POR CULTO"


def _calcular_reforma(fecha, F, G_adj, trab_h, des_h, dw, B, registros_todos, _culto):
    """
    Lógica de cálculo nueva desde la reforma del 15 de julio de 2026.
    Jornada = 7h. Nuevas categorías: HRFD, HRFN.

    Reglas:
    Normal (lun-sáb):
      06→14: 1 HED
      14→22: 2 RNO + 1 HEN
      22→06 lun-vie: 7 RNO + 1 HEN
      22→06 sáb: 2 RNO + 5 RFN + 1 HEFN
    Domingo normal:
      06→14: 8 HEFD
      14→22: 5 HEFD + 3 HEFN
      22→06: 5 RNO + 2 RFN + 1 HEN
    Dom 22→06 + lunes festivo: 7 RFN + 1 HEN
    Festivo lun-vie:
      06→14: 7 HRFD + 1 HEFD
      14→22: 5 HRFD + 2 HRFN + 1 HEFN
      22→06: 5 RNO + 2 HRFN + 1 HEN
    """
    res = dict(horas_trab=round(trab_h,2), hed=0.0, hen=0.0, rno=0.0,
               hefd=0.0, hefn=0.0, rfd=0.0, rfn=0.0, hrfd=0.0, hrfn=0.0,
               min_dia=round(trab_h*60))

    JORNADA = 7.0

    # Ajuste jornada para culto
    if _culto:
        if dw <= 4:   JORNADA = 9.0   # Lun-Jue
        elif dw == 5: JORNADA = 8.0   # Vie
        elif dw == 6: return res       # Sáb con culto = 0

    # ── DOMINGO NORMAL ──────────────────────────────────────────────────
    if dw == 7 and not B:
        sig_fest = _check_sig_fest(fecha, registros_todos)

        if F >= hn("06:00") and F < hn("14:00"):
            # 06→14: todo HEFD
            res["hefd"] = round(trab_h, 1)

        elif F >= hn("14:00") and F < hn("22:00"):
            # 14→22: 5 HEFD + 3 HEFN
            hefd_end = hn("19:00")
            res["hefd"] = round(max(0, (min(G_adj, hefd_end) - F) * 24), 1)
            res["hefn"] = round(max(0, (G_adj - max(F, hefd_end)) * 24), 1)

        elif F >= hn("22:00"):
            if sig_fest:
                # Dom 22→06 + lunes festivo: 7 RFN + 1 HEN
                rfn_end = hn("05:00") + 1
                res["rfn"] = round(max(0, (min(G_adj, rfn_end) - F) * 24), 1)
                if G_adj > rfn_end:
                    res["hen"] = round((G_adj - rfn_end) * 24, 1)
            else:
                # Dom 22→06 normal: 5 RNO + 2 RFN + 1 HEN
                rno_end = F + 5/24
                res["rno"] = round(max(0, (min(G_adj, rno_end) - F) * 24), 1)
                rfn_end = rno_end + 2/24
                res["rfn"] = round(max(0, (min(G_adj, rfn_end) - rno_end) * 24), 1)
                if G_adj > rfn_end:
                    res["hen"] = round((G_adj - rfn_end) * 24, 1)
        return res

    # ── FESTIVO (lun-vie) ─────────────────────────────────────────────
    if B and dw in [1,2,3,4,5]:
        if F >= hn("06:00") and F < hn("14:00"):
            # 06→14: 7 HRFD + 1 HEFD
            res["hrfd"] = round(min(trab_h, JORNADA), 1)
            res["hefd"] = round(max(0, trab_h - JORNADA), 1)

        elif F >= hn("14:00") and F < hn("22:00"):
            # 14→22: 5 HRFD + 2 HRFN + 1 HEFN
            fin_jornada = F + JORNADA/24
            hrfd_end = hn("19:00")
            res["hrfd"] = round(max(0, (min(fin_jornada, hrfd_end) - F) * 24), 1)
            hrfn_end = hn("21:00")
            res["hrfn"] = round(max(0, (min(fin_jornada, hrfn_end) - max(F, hrfd_end)) * 24), 1)
            if G_adj > fin_jornada:
                res["hefn"] = round((G_adj - fin_jornada) * 24, 1)

        elif F >= hn("22:00"):
            # 22→06: 5 RNO + 2 HRFN + 1 HEN
            fin_jornada = F + JORNADA/24
            rno_end = F + 5/24
            res["rno"] = round(max(0, (min(G_adj, rno_end) - F) * 24), 1)
            res["hrfn"] = round(max(0, (min(G_adj, fin_jornada) - rno_end) * 24), 1)
            if G_adj > fin_jornada:
                res["hen"] = round((G_adj - fin_jornada) * 24, 1)
        return res

    # ── FESTIVO SÁBADO ────────────────────────────────────────────────
    if B and dw == 6:
        if F >= hn("06:00") and F < hn("14:00"):
            res["hrfd"] = round(min(trab_h, JORNADA), 1)
            res["hefd"] = round(max(0, trab_h - JORNADA), 1)
        elif F >= hn("14:00") and F < hn("22:00"):
            fin_jornada = F + JORNADA/24
            hrfd_end = hn("19:00")
            res["hrfd"] = round(max(0, (min(fin_jornada, hrfd_end) - F) * 24), 1)
            hrfn_end = hn("21:00")
            res["hrfn"] = round(max(0, (min(fin_jornada, hrfn_end) - max(F, hrfd_end)) * 24), 1)
            if G_adj > fin_jornada:
                res["hefn"] = round((G_adj - fin_jornada) * 24, 1)
        elif F >= hn("22:00"):
            fin_jornada = F + JORNADA/24
            rno_end = F + 5/24
            res["rno"] = round(max(0, (min(G_adj, rno_end) - F) * 24), 1)
            res["hrfn"] = round(max(0, (min(G_adj, fin_jornada) - rno_end) * 24), 1)
            if G_adj > fin_jornada:
                res["hen"] = round((G_adj - fin_jornada) * 24, 1)
        return res

    # ── FESTIVO DOMINGO ───────────────────────────────────────────────
    if B and dw == 7:
        if F >= hn("06:00") and F < hn("14:00"):
            res["hefd"] = round(trab_h, 1)
        elif F >= hn("14:00") and F < hn("22:00"):
            hefd_end = hn("19:00")
            res["hefd"] = round(max(0, (min(G_adj, hefd_end) - F) * 24), 1)
            res["hefn"] = round(max(0, (G_adj - max(F, hefd_end)) * 24), 1)
        elif F >= hn("22:00"):
            rfn_end = hn("05:00") + 1
            res["rfn"] = round(max(0, (min(G_adj, rfn_end) - F) * 24), 1)
            if G_adj > rfn_end:
                res["hen"] = round((G_adj - rfn_end) * 24, 1)
        return res

    # ── NORMAL (lun-vie no festivo) ───────────────────────────────────
    if not B and dw in [1,2,3,4,5]:
        if F >= hn("06:00") and F < hn("14:00"):
            # Diurno: HED = horas sobre jornada
            res["hed"] = round(max(0, trab_h - JORNADA), 1)

        elif F >= hn("14:00") and F < hn("22:00"):
            # Tarde: RNO en zona 19:00-21:00 dentro jornada, HEN extra
            fin_jornada = F + JORNADA/24
            rno_start = hn("19:00"); rno_end_j = hn("21:00")
            res["rno"] = round(max(0, (min(fin_jornada, rno_end_j) - max(F, rno_start)) * 24), 1)
            if G_adj > fin_jornada:
                res["hen"] = round((G_adj - fin_jornada) * 24, 1)

        elif F >= hn("22:00"):
            # Noche: 7 RNO + 1 HEN
            fin_jornada = F + JORNADA/24
            res["rno"] = round(max(0, (min(G_adj, fin_jornada) - F) * 24), 1)
            if G_adj > fin_jornada:
                res["hen"] = round((G_adj - fin_jornada) * 24, 1)

        elif F < hn("06:00"):
            # Entrada antes de 06:00 → diurno con HEN pre-06:00
            extra = max(0, trab_h - JORNADA)
            if extra > 0:
                pre06 = max(0, (hn("06:00") - F) * 24)
                hen_part = min(extra, pre06)
                res["hen"] = round(hen_part, 1)
                res["hed"] = round(extra - hen_part, 1)
        return res

    # ── SÁBADO NORMAL ─────────────────────────────────────────────────
    if not B and dw == 6:
        if F >= hn("06:00") and F < hn("14:00"):
            # Sáb diurno: jornada 7h, extra = HED
            res["hed"] = round(max(0, trab_h - JORNADA), 1)

        elif F >= hn("14:00") and F < hn("22:00"):
            fin_jornada = F + JORNADA/24
            rno_start = hn("19:00"); rno_end_j = hn("21:00")
            res["rno"] = round(max(0, (min(fin_jornada, rno_end_j) - max(F, rno_start)) * 24), 1)
            if G_adj > fin_jornada:
                res["hen"] = round((G_adj - fin_jornada) * 24, 1)

        elif F >= hn("22:00"):
            # Sáb 22→06: 2 RNO + 5 RFN + 1 HEFN
            med = 1.0
            res["rno"] = round(max(0, (min(G_adj, med) - F) * 24), 1)
            rfn_end = hn("05:00") + 1
            res["rfn"] = round(max(0, (min(G_adj, rfn_end) - med) * 24), 1)
            if G_adj > rfn_end:
                res["hefn"] = round((G_adj - rfn_end) * 24, 1)

        elif F < hn("06:00"):
            # Sáb entrada antes 06:00
            extra = max(0, trab_h - JORNADA)
            if extra > 0:
                pre06 = max(0, (hn("06:00") - F) * 24)
                hen_part = min(extra, pre06)
                res["hen"] = round(hen_part, 1)
                res["hed"] = round(extra - hen_part, 1)
        return res

    return res


def calcular_fila(fecha, registro, obs_map, registros_todos=None):
    res=dict(horas_trab=0.0,hed=0.0,hen=0.0,rno=0.0,hefd=0.0,hefn=0.0,
             rfd=0.0,rfn=0.0,hrfd=0.0,hrfn=0.0,min_dia=0.0)
    entrada_s=registro.get("entrada",""); salida_s=registro.get("salida","")
    obs=(registro.get("observacion") or "").strip().upper()
    es_fest=registro.get("es_festivo",False)
    des_raw=registro.get("descanso") or 0
    des_h=des_raw/60.0 if des_raw>3 else float(des_raw)

    if not entrada_s or not salida_s:
        if obs and obs in obs_map:
            ob=obs_map[obs]
            if ob["cuenta_ot"] and ob["horas_fijas"]>0:
                res["horas_trab"]=ob["horas_fijas"]; res["min_dia"]=ob["horas_fijas"]*60
        return res

    F=to_dec(entrada_s); G=to_dec(salida_s); dw=diasem(fecha); B=es_fest
    G_adj=G+1 if G<F else G
    trab_h=(G_adj-F)*24-des_h
    if trab_h<=0: return res

    es_reforma = fecha >= REFORMA

    # ── NUEVA REFORMA ───────────────────────────────────────────────────
    if es_reforma:
        _culto = _check_culto(fecha, registros_todos)
        return _calcular_reforma(fecha, F, G_adj, trab_h, des_h, dw, B, registros_todos, _culto)

    # ── LÓGICA ANTERIOR AL 15 JUL 2026 ─────────────────────────────────
    res["horas_trab"]=round(trab_h,2); res["min_dia"]=round(trab_h*60)

    # Caso especial: entrada diurna (antes de 14:00) con salida que cruza noche
    if not B and F < hn("14:00") and G_adj > hn("22:00") and dw not in [6,7]:
        fin_diurno = hn("19:00")
        horas_diurnas = (min(G_adj, fin_diurno) - F) * 24 - des_h
        hed = max(0, round(horas_diurnas - 8.0, 1))
        res["hed"] = hed
        rno_fin = hn("06:00") + 1
        res["rno"] = round(max(0, (min(G_adj, rno_fin) - hn("22:00")) * 24), 1)
        res["hen"] = round(max(0, (min(G_adj, hn("22:00")) - hn("19:00")) * 24), 1)
        if G_adj > rno_fin:
            res["hed"] = round(res["hed"] + (G_adj - rno_fin) * 24, 1)
        return res

    # Verificar DESCANSO POR CULTO
    _culto = _check_culto(fecha, registros_todos)
    if _culto and dw <= 4:      _jornada = 9.0
    elif _culto and dw == 5:    _jornada = 8.0
    else:                        _jornada = 8.0

    # Caso especial: día normal 22:00→XX:XX cruzando hacia día festivo
    if not B and F >= hn("22:00") and G_adj > 1.0 and dw not in [6, 7]:
        _sig_fest = _check_sig_fest(fecha, registros_todos)
        if _sig_fest:
            res["rno"]  = round((1.0 - F) * 24, 1)
            res["rfn"]  = round(max(0, (min(G_adj, hn("06:00")+1) - 1.0)*24), 1)
            res["hefd"] = round(max(0, (G_adj - (hn("06:00")+1)) * 24), 1)
            return res

    _hen_set=False
    _rfn_set=False

    # HED
    if not B and entrada_s and salida_s:
        if dw==7: hed=0.0
        elif dw==6:
            if _culto: hed=0.0
            elif F==hn("06:00"): hed=(min(G_adj,hn("19:00"))-F)*24-4-des_h
            elif F==hn("14:00"): hed=1.0
            elif F==hn("07:00"): hed=max(0,(min(G_adj,hn("19:00"))-F)*24-_jornada-des_h)
            elif F<hn("06:00"):
                jornada_sab=4.0; g_cap=min(G_adj,hn("19:00"))
                if g_cap<=hn("06:00"): g_cap+=1
                diff=round((g_cap-F)*24-jornada_sab-des_h,4)
                if diff>0:
                    pre06=max(0,(hn("06:00")-F))*24; hen_part=min(diff,pre06)
                    res["hen"]=round(hen_part,1); _hen_set=True; hed=round(diff-hen_part,1)
                else: hed=-math.ceil(abs(diff)) if diff<0 else max(0,diff)
            elif F<hn("14:00"):
                jornada_sab=4.0; g_cap=min(G_adj,hn("19:00"))
                diff=round((g_cap-F)*24-jornada_sab-des_h,4); hed=max(0,diff)
            else: hed=0.0
        elif F==hn("22:00"): hed=max(0,(G-hn("06:00"))*24-des_h) if G>hn("06:00") else 0.0
        elif F==hn("07:00"):
            diff=round((min(G_adj,hn("19:00"))-F)*24-_jornada-des_h,4)
            hed=-math.ceil(abs(diff)) if diff<0 else max(0,diff)
        elif F<hn("14:00"):
            g_cap=min(G_adj,hn("19:00"))
            if g_cap<=hn("06:00"): g_cap+=1
            diff=round((g_cap-F)*24-_jornada-des_h,4)
            if F<hn("06:00") and diff>0:
                pre06=max(0,(hn("06:00")-F))*24; hen_part=min(diff,pre06)
                res["hen"]=round(hen_part,1); _hen_set=True; hed=round(diff-hen_part,1)
            else: hed=-math.ceil(abs(diff)) if diff<0 else max(0,diff)
        else: hed=0.0
        res["hed"]=hed if isinstance(hed,int) else round(hed,1)

    # HEN
    if not B and entrada_s and salida_s and not _hen_set:
        if F==hn("06:00") and G_adj>hn("19:00"): hen=(G_adj-hn("19:00"))*24
        elif dw==6 and F==hn("22:00") and G==hn("06:00"): hen=0.0
        elif dw==6:
            hen=max(0,(min(G_adj,hn("22:00"))-hn("19:00"))*24) if hn("14:00")<=F<hn("22:00") else 0.0
        elif dw==5 and F>=hn("22:00"):
            v=(G_adj-hn("30:00"))*24; hen=0.0 if v>=24 else max(0,v)
        elif hn("14:00")<=F<hn("22:00"):
            hen=max(0,(min(G_adj,hn("22:00"))-hn("22:00"))*24)
        else: hen=0.0
        res["hen"]=round(max(0,hen),1)

    # RNO
    if entrada_s and salida_s:
        if F>=1.0:
            res["rno"]=round(max(0,(G_adj-F)*24-des_h),1); return res
        if dw==5 and F==hn("22:00") and not B:
            dom_fecha = fecha - timedelta(days=5)
            reg_dom=(registros_todos or {}).get(dom_fecha,{}) or (registros_todos or {}).get(dom_fecha.isoformat(),{})
            if isinstance(reg_dom, list): reg_dom = reg_dom[0] if reg_dom else {}
            dom_entrada=reg_dom.get("entrada","")
            if dom_entrada and to_dec(dom_entrada)==hn("22:00"):
                rno=4.0; res["hen"]=4.0
            else:
                rno=max(0,(min(G_adj,hn("06:00")+1)-hn("22:00"))*24)
        elif dw==5 and F==hn("22:00") and B:
            rno=max(0,(min(G_adj,hn("06:00")+1)-1)*24)
        elif dw==6 and F==hn("22:00"): rno=max(0,(min(G_adj,1.0)-hn("22:00"))*24)
        elif dw==6: rno=0.0
        elif dw==7 and F==hn("22:00"):
            _lun_fest = _check_sig_fest(fecha, registros_todos)
            if _lun_fest:
                rno = 0.0
                res["rfn"] = round((1.0 - F) * 24 + max(0, (G_adj - 1.0) * 24), 1)
                _rfn_set = True
            else:
                rno=max(0,(G_adj-1.0)*24)
        elif dw==7: rno=0.0
        elif B:
            rno=max(0,(min(G_adj,hn("06:00")+1)-1)*24) if F>=hn("22:00") else 0.0
        elif F<hn("14:00"): rno=0.0
        elif hn("14:00")<=F<hn("22:00"):
            if G_adj > 1.0:
                rno = max(0, (min(G_adj, hn("06:00")+1) - hn("22:00")) * 24)
                if G_adj > hn("06:00")+1:
                    res["hen"] = round((G_adj - (hn("06:00")+1)) * 24, 1)
                    res["hed"] = round((G_adj - (hn("06:00")+1)) * 24, 1)
            elif G_adj > hn("22:00"):
                rno = 2.0 if False else max(0, (hn("22:00") - hn("19:00")) * 24)
                res["hen"] = round((G_adj - hn("22:00")) * 24, 1)
            else:
                rno = max(0, (min(G_adj, hn("22:00")) - hn("19:00")) * 24)
        else: rno=max(0,(min(G_adj,hn("06:00")+1)-hn("22:00"))*24)
        res["rno"]=round(max(0,rno),1)

    # HEFD
    if entrada_s and salida_s:
        if dw==7:
            hefd=max(0,round((min(G_adj,hn("19:00"))-F)*24-des_h,2)) if F<hn("22:00") else 0.0
        elif B:
            hefd=0.0 if F==hn("22:00") else max(0,round((min(G_adj,hn("19:00"))-(F+8/24))*24-des_h,2))
        else: hefd=0.0
        res["hefd"]=round(max(0,hefd),1)

    # HEFN
    if entrada_s and salida_s:
        if dw==6 and F==hn("22:00"): hefn=max(0,(G_adj-hn("02:00")-1)*24)
        elif dw==7:
            hefn=0.0 if F>=hn("22:00") else max(0,(G_adj-hn("19:00"))*24)
        elif B and (G_adj-F)*24>8:
            if F==hn("22:00"): hefn=0.0
            elif F==hn("14:00"): hefn=max(0,(min(G_adj,hn("06:00")+1)-hn("22:00"))*24)
            else: hefn=max(0,(G_adj-hn("19:00"))*24)
        else: hefn=0.0
        res["hefn"]=round(max(0,hefn),1)

    # RFD
    if entrada_s and salida_s and B:
        if F<hn("14:00"): rfd=min(8,max(0,(min(G_adj,hn("19:00"))-F)*24))
        elif hn("14:00")<=F<hn("22:00"): rfd=min(8,max(0,(min(G_adj,hn("19:00"))-hn("14:00"))*24))
        else: rfd=0.0
        res["rfd"]=round(max(0,rfd),1)

    # RFN
    if entrada_s and salida_s and not _rfn_set:
        if dw==6 and F==hn("22:00"): rfn=max(0,(min(G_adj,hn("02:00")+1)-1)*24)
        elif dw==7 and F>=hn("22:00"): rfn=(1.0-F)*24
        elif B:
            if hn("14:00")<=F<hn("22:00"): rfn=max(0,(min(G_adj,hn("22:00"))-hn("19:00"))*24)
            elif F>=hn("22:00"): rfn=max(0,(min(G_adj+1,1.0)-hn("22:00"))*24)
            else: rfn=0.0
        else: rfn=0.0
        res["rfn"]=round(max(0,rfn),1)

    return res


def clasificar_dia(fecha,registro,min_acum_semana,cfg,es_culto,obs_map,registros_todos=None):
    return calcular_fila(fecha,registro,obs_map)


def calcular_semana(dias,registros,cfg,obs_map):
    min_acum=0.0; rows=[]
    for fecha in dias:
        reg=registros.get(fecha,{})
        res=calcular_fila(fecha,reg,obs_map,registros_todos=registros)
        rows.append({"fecha":fecha,"resultado":res,"registro":reg})
        min_acum+=res["min_dia"]
    return {"rows":rows,"ot_semana":round(min_acum/60-cfg["horas_sem"],1),"horas_semana":round(min_acum/60,1)}


def calcular_periodo(year,month,registros,cfg,obs_map):
    inicio=date(year,month,21)
    mes_fin=month+1 if month<12 else 1
    año_fin=year if month<12 else year+1
    fin=date(año_fin,mes_fin,20)
    dias=[]; d=inicio
    while d<=fin: dias.append(d); d+=timedelta(days=1)
    semanas={}
    for d in dias:
        dow=d.weekday(); dom=d if dow==6 else d-timedelta(days=dow+1)
        if dom not in semanas: semanas[dom]=[]
        semanas[dom].append(d)
    semanas_result=[]
    for dom in sorted(semanas.keys()):
        res=calcular_semana(semanas[dom],registros,cfg,obs_map)
        semanas_result.append({"lunes":dom,**res})
    sub=dict(hed=0.0,hen=0.0,rno=0.0,hefd=0.0,hefn=0.0,rfd=0.0,rfn=0.0,
             hrfd=0.0,hrfn=0.0,horas_total=0.0,ot_total=0.0)
    for sem in semanas_result:
        sub["ot_total"]+=sem["ot_semana"]; sub["horas_total"]+=sem["horas_semana"]
        for row in sem["rows"]:
            for col in ["hed","hen","rno","hefd","hefn","rfd","rfn","hrfd","hrfn"]:
                sub[col]+=row["resultado"].get(col,0)
    for k in sub: sub[k]=round(sub[k],1)
    return {"semanas":semanas_result,"subtotales":sub,"dias":[d.isoformat() for d in dias],
            "inicio":inicio.isoformat(),"fin":fin.isoformat()}


FACTORES={"hed":1.25,"hen":1.75,"rno":0.35,"hefd":2.05,"hefn":2.55,
          "rfd":0.80,"rfn":1.15,"hrfd":0.80,"hrfn":1.15}

def get_factores_fecha(fecha, factores_config=None):
    f = dict(factores_config) if factores_config else dict(FACTORES)
    if fecha < REFORMA_RFD:
        f["rfd"] = 0.80; f["hrfd"] = 0.80
    else:
        f["rfd"]  = factores_config.get("rfd",  0.90) if factores_config else 0.90
        f["hrfd"] = factores_config.get("hrfd", 0.90) if factores_config else 0.90
    return f

def get_horas_sem_fecha(fecha, horas_sem_config):
    return 42.0 if fecha >= REFORMA else horas_sem_config

def calcular_valores(sueldo, horas_sem, subtotales, factores=None, fecha=None):
    hs = get_horas_sem_fecha(fecha, horas_sem) if fecha else horas_sem
    jornada_mensual=round((hs/6)*30)
    vh=sueldo/jornada_mensual; res={}; neto=0.0
    f_map = factores if factores else FACTORES
    for col, f in FACTORES.items():
        factor = f_map.get(col, f)
        v=round(subtotales.get(col,0.0)*vh*factor,2); res[f"val_{col}"]=v; neto+=v
    res["neto"]=round(neto,2); res["valor_hora"]=round(vh,2)
    return res

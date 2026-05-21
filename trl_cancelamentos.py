"""
TRL — Análise de Cancelamentos por Motivo Financeiro
Metodologia: Teorema da Renda Livre | Trium Mind Advisory
Autor: Márcio Santos / ODDATA
-------------------------------------------------------------
Uso:
    python trl_cancelamentos.py --input base_cancelados.csv --output resultado_trl.csv

Colunas esperadas no CSV de entrada:
    idcontrato, idcasal, datacancelamento, valorcontrato,
    rendafamiliar, statuscivil, uf, vlparcela
"""

import pandas as pd
import argparse
import sys
import os
from pathlib import Path

# ─── Configurações de caminho ───────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
DATA_DIR     = BASE_DIR / "data"
CLASSES_CSV  = DATA_DIR / "classes.csv"
CV_CSV       = DATA_DIR / "custo_vida.csv"

# ─── Carregamento dos parâmetros TRL ────────────────────────────────────────
def carregar_parametros():
    if not CLASSES_CSV.exists() or not CV_CSV.exists():
        print("❌ Arquivos de parâmetros não encontrados em /data.")
        print("   Certifique-se de que classes.csv e custo_vida.csv estão na pasta /data.")
        sys.exit(1)

    classes   = pd.read_csv(CLASSES_CSV)
    custo_vid = pd.read_csv(CV_CSV).set_index("uf")["custo_vida"].to_dict()
    return classes, custo_vid


# ─── Classificação por classe social ────────────────────────────────────────
def classificar_classe(rbf, classes_df):
    for _, row in classes_df.iterrows():
        if row["rbf_min"] <= rbf <= row["rbf_max"]:
            return row
    return None


# ─── Cálculo do TRL para um contrato ────────────────────────────────────────
def calcular_trl(row, classes_df, custo_vida_dict):
    rbf       = row["rendafamiliar"]
    uf        = str(row["uf"]).strip().upper()
    vlparcela = row["vlparcela"]

    # Custo de vida da UF
    cv = custo_vida_dict.get(uf)
    if cv is None:
        return {
            "classe": "INDEFINIDA",
            "cc": None, "cv": None, "rs": None,
            "rld": None, "impacto_parcela_perc": None,
            "zona": "UF_NAO_ENCONTRADA",
            "parcela_max_segura": None,
            "excesso_sobre_max": None,
            "elegivel": False,
        }

    # Classificar classe
    classe_row = classificar_classe(rbf, classes_df)
    if classe_row is None:
        return {
            "classe": "FORA_FAIXA",
            "cc": None, "cv": cv, "rs": None,
            "rld": None, "impacto_parcela_perc": None,
            "zona": "FORA_FAIXA",
            "parcela_max_segura": None,
            "excesso_sobre_max": None,
            "elegivel": False,
        }

    classe     = classe_row["classe"]
    cc_perc    = classe_row["cc_perc"]
    rs_perc    = classe_row["rs_perc"]
    fl_min     = classe_row["fl_min"]
    fl_max     = classe_row["fl_max"]
    elegivel   = bool(classe_row["elegivel"])

    # Fórmula TRL
    cc  = round(rbf * cc_perc, 2)
    rs  = round(rbf * rs_perc, 2)
    rld = round(rbf - cc - cv - rs, 2)

    if not elegivel or rld < 500:
        return {
            "classe": classe,
            "cc": cc, "cv": cv, "rs": rs,
            "rld": rld,
            "impacto_parcela_perc": None,
            "zona": "FORA_DO_ESCOPO",
            "parcela_max_segura": None,
            "excesso_sobre_max": None,
            "elegivel": elegivel,
        }

    # Impacto da parcela sobre a RLD
    impacto_perc      = round((vlparcela / rld) * 100, 2)
    parcela_max_segura = round(rld * fl_max, 2)
    excesso_sobre_max  = round(vlparcela - parcela_max_segura, 2)

    # Zona de impacto
    if impacto_perc <= fl_min * 100:
        zona = "VERDE"          # parcela confortável
    elif impacto_perc <= fl_max * 100:
        zona = "AMARELA"        # parcela no limite aceitável
    elif impacto_perc <= 50:
        zona = "VERMELHA"       # risco alto — parcela acima do envelope
    else:
        zona = "CRITICA"        # parcela inviável — acima de 50% da RLD

    return {
        "classe": classe,
        "cc": cc,
        "cv": cv,
        "rs": rs,
        "rld": rld,
        "impacto_parcela_perc": impacto_perc,
        "zona": zona,
        "parcela_max_segura": parcela_max_segura,
        "excesso_sobre_max": excesso_sobre_max if excesso_sobre_max > 0 else 0.0,
        "elegivel": elegivel,
    }


# ─── Processamento principal ─────────────────────────────────────────────────
def processar(input_path: str, output_path: str):
    print(f"\n📂 Lendo base: {input_path}")
    try:
        df = pd.read_csv(input_path, sep=None, engine="python")
    except Exception as e:
        print(f"❌ Erro ao ler CSV: {e}")
        sys.exit(1)

    # Validação de colunas obrigatórias
    colunas_obrigatorias = {"rendafamiliar", "uf", "vlparcela"}
    faltando = colunas_obrigatorias - set(df.columns.str.lower())
    if faltando:
        print(f"❌ Colunas obrigatórias ausentes: {faltando}")
        sys.exit(1)

    df.columns = df.columns.str.lower()

    print(f"✅ {len(df)} contratos carregados.")
    print("⚙️  Calculando TRL...\n")

    classes_df, custo_vida_dict = carregar_parametros()

    resultados = df.apply(
        lambda row: calcular_trl(row, classes_df, custo_vida_dict),
        axis=1,
        result_type="expand",
    )

    df_out = pd.concat([df, resultados], axis=1)

    # Salvar CSV completo
    df_out.to_csv(output_path, index=False)
    print(f"💾 Resultado salvo em: {output_path}\n")

    # ─── Relatório no terminal ───────────────────────────────────────────
    print("=" * 62)
    print("  ANÁLISE TRL — CANCELAMENTOS POR IMPACTO FINANCEIRO")
    print("  Metodologia: Trium Mind Advisory | Trl-Renda-Livre")
    print("=" * 62)

    total = len(df_out)
    com_rld = df_out[df_out["rld"].notna()]
    sem_rld = total - len(com_rld)

    print(f"\n  Total de contratos analisados : {total}")
    print(f"  Com cálculo TRL válido        : {len(com_rld)}")
    print(f"  Fora do escopo / UF inválida  : {sem_rld}")

    if len(com_rld) == 0:
        print("\n  ⚠️  Nenhum contrato com cálculo válido.")
        return

    # Distribuição por zona
    print("\n  DISTRIBUIÇÃO POR ZONA DE IMPACTO:")
    print("  ─────────────────────────────────────────────────────")
    zonas = com_rld["zona"].value_counts()
    ordem_zonas = ["VERDE", "AMARELA", "VERMELHA", "CRITICA", "FORA_DO_ESCOPO"]
    emojis = {"VERDE": "🟢", "AMARELA": "🟡", "VERMELHA": "🔴", "CRITICA": "⛔", "FORA_DO_ESCOPO": "⚪"}

    for zona in ordem_zonas:
        qtd = zonas.get(zona, 0)
        perc = qtd / total * 100
        print(f"  {emojis.get(zona,'')} {zona:<18} {qtd:>5} contratos  ({perc:.1f}%)")

    # Estatísticas de impacto por zona
    print("\n  IMPACTO MÉDIO DA PARCELA SOBRE A RLD (por zona):")
    print("  ─────────────────────────────────────────────────────")
    zonas_risco = ["VERMELHA", "CRITICA"]
    analise = com_rld[com_rld["zona"].isin(["VERDE","AMARELA","VERMELHA","CRITICA"])]
    if not analise.empty:
        resumo = (
            analise.groupby("zona")["impacto_parcela_perc"]
            .agg(["mean","min","max","count"])
            .rename(columns={"mean":"Média %","min":"Mínimo %","max":"Máximo %","count":"Qtd"})
        )
        for zona, row in resumo.iterrows():
            print(f"  {emojis.get(zona,'')} {zona:<18}  média {row['Média %']:>6.1f}%  |  min {row['Mínimo %']:>6.1f}%  |  max {row['Máximo %']:>6.1f}%  |  {int(row['Qtd'])} contratos")

    # Distribuição por classe
    print("\n  DISTRIBUIÇÃO POR CLASSE SOCIAL:")
    print("  ─────────────────────────────────────────────────────")
    for classe, qtd in com_rld["classe"].value_counts().items():
        print(f"  {'':2} {classe:<10} {qtd:>5} contratos")

    # Casos críticos e vermelhos com excesso de parcela
    risco = com_rld[com_rld["zona"].isin(zonas_risco)].copy()
    if not risco.empty:
        print(f"\n  ⚠️  CONTRATOS EM ZONA VERMELHA / CRÍTICA: {len(risco)}")
        print("  ─────────────────────────────────────────────────────")
        print(f"  Excesso médio acima da parcela máxima segura: "
              f"R$ {risco['excesso_sobre_max'].mean():,.2f}")
        print(f"  Excesso máximo registrado                  : "
              f"R$ {risco['excesso_sobre_max'].max():,.2f}")
        print(f"  RLD médio desse grupo                      : "
              f"R$ {risco['rld'].mean():,.2f}")
        print(f"  Impacto médio parcela/RLD                  : "
              f"{risco['impacto_parcela_perc'].mean():.1f}%")

    print("\n" + "=" * 62)
    print("  Colunas geradas no CSV de saída:")
    print("  classe | cc | cv | rs | rld | impacto_parcela_perc")
    print("  zona   | parcela_max_segura | excesso_sobre_max")
    print("=" * 62 + "\n")


# ─── Entrypoint ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Análise de cancelamentos com o Teorema da Renda Livre (TRL)"
    )
    parser.add_argument("--input",  required=True, help="Caminho do CSV de entrada")
    parser.add_argument("--output", default="output/resultado_trl.csv", help="Caminho do CSV de saída")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    processar(args.input, args.output)

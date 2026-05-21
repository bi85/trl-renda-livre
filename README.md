# TRL — Teorema da Renda Livre
Teorema da Renda Livre — metodologia open source para análise de capacidade de pagamento em multipropriedade e timeshare

> *"Não existe parcela cara. Existe parcela fora do envelope."*

Metodologia open source para calcular a **Renda Livre Disponível (RLD)** de compradores de produtos imobiliários parcelados — e determinar se uma parcela cabe no orçamento real de quem está assinando o contrato.

Desenvolvida e mantida por **Márcio Santos** ([Trium Mind Advisory](https://mindtrium.com.br) / [ODDATA](https://oddata.com.br)), com 13 anos de aplicação em operações de multipropriedade, timeshare e incorporação imobiliária no Brasil.

---

## O problema que o TRL resolve

O mercado de multipropriedade e timeshare tem um problema crônico: **vende para quem não pode pagar**.

Não por má-fé. Por ausência de metodologia. O vendedor olha para a renda declarada e decide na intuição se a parcela cabe. O resultado aparece 6, 12, 18 meses depois — no índice de cancelamento por motivo financeiro.

O TRL torna esse julgamento calculável, auditável e replicável.

---

## A fórmula

```
RBF   Renda Bruta Familiar Mensal
- CC  Comprometimento com Crédito Existente  (22% a 35% conforme classe)
- CV  Custo de Vida Local Ajustado            (por UF, fonte IBREP)
- RS  Reserva de Segurança                    (10% da RBF)
────
RLD   Renda Livre Disponível

Parcela Máxima Segura = RLD × Fator de Lazer (FL)
```

O **Fator de Lazer** representa a fração da RLD que o comprador aceita comprometer com um produto de lazer recorrente. Varia de 10% (classe C2) a 30% (classe A), calibrado por comportamento real de compra no setor.

---

## Zonas de impacto

| Zona | Condição | Interpretação |
|------|----------|---------------|
| 🟢 Verde | Parcela ≤ RLD × FL_mínimo | Parcela confortável — baixo risco |
| 🟡 Amarela | FL_mínimo < Parcela ≤ FL_máximo | Parcela no limite — requer atenção |
| 🔴 Vermelha | FL_máximo < Parcela ≤ 50% RLD | Risco alto — candidato a cancelamento |
| ⛔ Crítica | Parcela > 50% da RLD | Inviável — cancelamento provável |

---

## Parâmetros

Os parâmetros da metodologia ficam em `/data` e podem ser atualizados independentemente do código:

- `data/classes.csv` — faixas de renda por classe social, CC%, RS% e Fator de Lazer (fonte: FGV Social / Bacen SCR)
- `data/custo_vida.csv` — custo médio mensal por UF (fonte: IBREP, atualização anual)

Isso significa que quando o IBREP publica novos dados, você atualiza uma linha no CSV — sem tocar no código.

---

## Como usar

### Instalação

```bash
git clone https://github.com/seu-usuario/trl-renda-livre.git
cd trl-renda-livre
pip install pandas
```

### Rodando na sua base

```bash
python trl_cancelamentos.py --input sua_base.csv --output resultado_trl.csv
```

### Colunas esperadas no CSV de entrada

| Coluna | Tipo | Descrição |
|--------|------|-----------|
| `rendafamiliar` | float | Renda bruta familiar mensal (R$) |
| `uf` | string | UF de origem do comprador (ex: SP, MG) |
| `vlparcela` | float | Valor da parcela contratada (R$) |

As demais colunas (idcontrato, nome, data etc.) são opcionais e passam intactas para o CSV de saída.

### Colunas geradas no CSV de saída

| Coluna | Descrição |
|--------|-----------|
| `classe` | Classe social enquadrada (A, B1, B2, C1, C2, D, E) |
| `cc` | Comprometimento com crédito calculado (R$) |
| `cv` | Custo de vida da UF (R$) |
| `rs` | Reserva de segurança (R$) |
| `rld` | Renda Livre Disponível (R$) |
| `impacto_parcela_perc` | Parcela como % da RLD |
| `zona` | Verde / Amarela / Vermelha / Crítica / Fora do Escopo |
| `parcela_max_segura` | Teto recomendado pela metodologia (R$) |
| `excesso_sobre_max` | Quanto a parcela ultrapassa o teto (R$) |

---

## Exemplo de saída

```
==============================================================
  ANÁLISE TRL — CANCELAMENTOS POR IMPACTO FINANCEIRO
  Metodologia: Trium Mind Advisory | Trl-Renda-Livre
==============================================================

  Total de contratos analisados : 1.847
  Com cálculo TRL válido        : 1.831

  DISTRIBUIÇÃO POR ZONA DE IMPACTO:
  ─────────────────────────────────────────────────
  🟢 VERDE        912 contratos  (49.4%)
  🟡 AMARELA      487 contratos  (26.4%)
  🔴 VERMELHA     318 contratos  (17.2%)
  ⛔ CRITICA      114 contratos   (6.2%)
  ⚪ FORA_DO_ESCOPO 16 contratos  (0.9%)

  ⚠️  CONTRATOS EM ZONA VERMELHA / CRÍTICA: 432
  Excesso médio acima da parcela máxima segura: R$ 847,23
  Impacto médio parcela/RLD: 41.8%
==============================================================
```

---

## Integração com PostgreSQL

O diretório `sql/` contém views prontas para rodar na base do cliente:

```sql
-- Calcula RLD e zona para toda a base de leads
SELECT * FROM vm_trl_resultado_leads;

-- Visão por praça (UF)
SELECT * FROM vm_trl_calculo;
```

---

## Estrutura do repositório

```
trl-renda-livre/
├── README.md
├── LICENSE                        ← MIT (código) + CC-BY (metodologia)
├── CHANGELOG.md
│
├── data/
│   ├── classes.csv                ← parâmetros por classe social
│   ├── custo_vida.csv             ← custo de vida por UF (IBREP)
│   └── leads_anonimos.csv         ← dataset sintético de exemplo
│
├── trl_cancelamentos.py           ← script principal
│
├── sql/
│   ├── schema.sql                 ← DDL das tabelas de parâmetros
│   └── views.sql                  ← views para PostgreSQL
│
├── notebooks/
│   └── exemplo_trl.ipynb          ← demo Colab-ready
│
└── docs/
    └── metodologia.md             ← explicação formal para citação
```

---

## Licença

- **Código:** [MIT License](LICENSE) — use, modifique, distribua.
- **Metodologia (TRL):** [Creative Commons BY 4.0](https://creativecommons.org/licenses/by/4.0/) — pode aplicar, mas precisa citar: *"Teorema da Renda Livre (TRL) — Márcio Santos / Trium Mind Advisory"*.

---

## Contribuindo

Issues e PRs são bem-vindos, especialmente para:

- Atualização dos dados de custo de vida por UF
- Novos adaptadores de entrada (Excel, PostgreSQL direto, API)
- Notebooks de análise exploratória
- Casos de uso documentados

---

## Autor

**Márcio Santos**
Consultor de dados e viabilidade para Real Estate e multipropriedade.
13 anos de operação no setor. Fundador da [ODDATA](https://oddata.com.br) e co-fundador da [Trium Mind Advisory](https://triummind.com.br).

[LinkedIn](https://linkedin.com/in/marciosantos) · [Instagram @triummind](https://instagram.com/triummind)

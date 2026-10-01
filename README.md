# add_reference (AI Knowledge Librarian v2.0)

[![CI](https://github.com/marcelomaymone/add_reference/actions/workflows/ci.yml/badge.svg)](https://github.com/marcelomaymone/add_reference/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Antigravity Skill](https://img.shields.io/badge/Antigravity-Skill%20Ready-purple.svg)](https://github.com/marcelomaymone/add_reference)

> **AI Knowledge Librarian v2.0:** Skill autônoma de ingestão, fatoração e catalogação de conhecimento normativo e técnico para agentes de Inteligência Artificial com arquitetura piramidal multi-tier, resumos executivos normativos e busca cirúrgica sem risco de estouro de contexto.

---

## 🏛️ Visão Geral e Propósito

Quando agentes de IA (LLMs) consom documentos técnicos extensos (como normas ISO/IEC/IEEE, manuais de engenharia, especificações regulatórias de dezenas ou centenas de páginas), dois problemas críticos ocorrem:
1. **Estouro de Janela de Contexto & Degradação da Atenção:** Documentos brutos esgotam a janela de tokens e induzem alucinações.
2. **Poluição por Metadados Residuais:** Marcadores de páginas, quebras arbitrárias e marcas d'água corrompem a leitura de tabelas e cláusulas.

A **`add_reference`** implementa o protocolo **AI Knowledge Librarian v2.0**, estruturando todo o conhecimento em uma **Arquitetura em Pirâmide Multi-Tier** armazenada no diretório `.referencias` de qualquer projeto.

```
                      ▲
                     / \
                    /   \     Tier 0: Catálogo & Índice Mestre (index.md)
                   / Tier\    Taxonomia global, matriz léxica rápida (< 450 linhas)
                  /   0   \
                 /─────────\
                /  Tier 1   \   Tier 1: Executive Brief (*_executive_brief.md)
               /             \  Regras mandatórias ('shall/must'), léxico e escopo (< 300 linhas)
              /───────────────\
             /     Tier 2      \  Tier 2: Recortes Fatorados Semânticos (*_01.md, *_02.md)
            /                   \ Particionamento boundary-aware com Frontmatter YAML (< 450 linhas)
           /─────────────────────\
```

---

## 🚀 Instalação Rápida (Global no Host)

A skill pode ser instalada diretamente no catálogo global do seu host, ficando imediatamente disponível para todas as instâncias do **Antigravity** e agentes compatíveis.

### Opção 1: Via Git Clone Direto (Recomendado)

#### Windows (PowerShell)
```powershell
git clone https://github.com/marcelomaymone/add_reference.git "$HOME\.gemini\config\skills\add_reference"
```

#### Linux / macOS (Bash)
```bash
git clone https://github.com/marcelomaymone/add_reference.git ~/.gemini/config/skills/add_reference
```

---

### Opção 2: Via Script Instalador Automatizado

Clone o repositório em qualquer pasta temporária e execute o instalador:

#### Windows (PowerShell)
```powershell
git clone https://github.com/marcelomaymone/add_reference.git
cd add_reference
.\install.ps1
```
*Opcionais:*
- `.\install.ps1 -Workspace` para instalar localmente no projeto (`.agents/skills/add_reference`).
- `.\install.ps1 -DryRun` para simular as etapas sem alterar arquivos.

#### Linux / macOS (Bash)
```bash
git clone https://github.com/marcelomaymone/add_reference.git
cd add_reference
chmod +x install.sh
./install.sh
```
*Opcionais:*
- `./install.sh --workspace` para instalar localmente no projeto.

---

## 📦 Instalação Local por Workspace (Projeto Individual)

Se preferir versionar a skill restrita a um único repositório:

```bash
git clone https://github.com/marcelomaymone/add_reference.git .agents/skills/add_reference
```

---

## 🎯 Gatilhos de Acionamento (Triggers)

No chat com o agente de IA:
- **Comando Direto:** `/add_reference`
- **Linguagem Natural:**
  - *"Adicione o arquivo norma_iso.pdf como referência"*
  - *"Cadastre esta planilha no catálogo de referências"*
  - *"Use a documentação técnica anexa como referência corporativa"*
  - *"Consulte o catálogo de referências do projeto"*

---

## ⚙️ Regras Invioláveis do Mecanismo

1. **Limite Estrito de 450 Linhas por Arquivo Markdown:** Nenhum arquivo de referência ultrapassa 450 linhas. Se exceder, é fatorado semanticamente (`_01.md`, `_02.md`, etc.).
2. **Executive Brief Normativo Obrigatório (Tier 1):** Documentos fatorados geram um irmão `*_executive_brief.md` com limite de **300 linhas**, contendo escopo, regras mandatórias (*"shall/must"*), entregáveis e a Matriz Léxica Remissiva.
3. **Particionamento Semântico Boundary-Aware:** Quebras nunca cortam tabelas, listas ou blocos de código ao meio, respeitando títulos (`#`, `##`, `###`).
4. **Metadados em YAML Frontmatter:** Cada partição contém cabeçalho estruturado (`document`, `part`, `total_parts`, `clauses`, `key_topics`, `upstream_references`).
5. **Eliminação Estrita de Marcadores de Página:** Expurgo automático de `<!-- Página X -->`, `\x0c`, numerações isoladas e marcas d'água (ex: IEEE Xplore).
6. **Catálogo & Índice Mestre (Tier 0):** O arquivo `index.md` resume taxonomicamente todas as referências com links diretos aos resumos e às partições. Se exceder 450 linhas, converte-se em índice particionado.
7. **Arquivamento Seguro:** Mídias e binários originais são organizados em `.referencias/docs_originais/`.

---

## 🔍 Busca Cirúrgica via Terminal (Zero Context Overhead)

Qualquer agente ou desenvolvedor pode realizar buscas diretas por palavras-chave, números de seções ou cláusulas sem ler os arquivos na íntegra:

```powershell
python "<caminho_da_skill>/scripts/convert_to_md.py" --query "5.2.1" ".referencias"
```

Saída estruturada:
```json
{
  "status": "success",
  "query": "5.2.1",
  "matches_count": 3,
  "results": [
    {
      "file": "iso_29148_02.md",
      "line_number": 84,
      "preview": "### 5.2.1 Stakeholder Identification Process"
    }
  ]
}
```

---

## 🛠️ CLI do Conversor (`convert_to_md.py`)

```text
Uso: convert_to_md.py [-h] [--name NAME] [--title TITLE] [--lang LANG] [--update-index] [--query QUERY] [source] [target_dir]

Argumentos Posicionais:
  source         Arquivo de entrada (.pdf, .docx, .xlsx, .md, .txt) ou '-' para stdin
  target_dir     Diretório .referencias de destino

Argumentos Opcionais:
  --name NAME          Nome base em snake_case_down (obrigatório se ler de stdin)
  --title TITLE        Título formal do documento
  --lang LANG          Idioma de saída do documento (padrão: eng-US)
  --update-index       Atualiza ou cria automaticamente o catálogo index.md
  --query QUERY        Executa busca cirúrgica sem converter arquivos
```

---

## 🧪 Testes Automatizados

O repositório inclui uma suíte abrangente com 9 testes unitários cobrindo sanitização de texto, particionamento semântico, YAML frontmatter, geração de índice e manipulação de fluxos:

```bash
python scripts/test_convert_to_md.py
```

---

## 📂 Formatos Suportados

| Formato | Mecanismo de Extração | Tratamento Especial |
| :--- | :--- | :--- |
| **PDF** (`.pdf`) | `pypdf` | Remoção de cabeçalhos de página, rodapés e marcas d'água |
| **Word** (`.docx`) | `python-docx` | Conversão de títulos estruturados e tabelas Markdown |
| **Excel** (`.xlsx`, `.xls`) | `pandas`, `openpyxl`, `tabulate` | Conversão de abas e tabelas com formatação Markdown alinhada |
| **Markdown / Texto** (`.md`, `.txt`) | Nativo | Fatoração em 450 linhas, YAML frontmatter e Executive Brief |
| **Stdin (Puro texto)** | Stream pipe | Entrada para transcrições e blocos colados diretamente |

---

## 📄 Licença

Distribuído sob a licença **MIT**. Consulte o arquivo [LICENSE](LICENSE) para mais informações.

Desenvolvido por **[Marcelo Maymone](https://github.com/marcelomaymone)**.

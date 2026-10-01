---
name: add_reference
description: "Ingere e cataloga referências (.pdf, .docx, .xlsx, .md) na pasta .referencias do workspace com arquitetura pirâmide multi-tier, executive briefs normativos, frontmatter YAML, busca cirúrgica e protocolo de recuperação para agentes."
---

# SKILL: add_reference (AI Knowledge Librarian v2.0)

Você é o **Bibliotecário de Conhecimento de IA** (*AI Knowledge Librarian*). Sua função essencial é ingerir, converter, catalogar e organizar artefatos normativos e de conhecimento corporativo em uma **Arquitetura em Pirâmide Multi-Tier** de alto desempenho no diretório `.referencias` do workspace.

O objetivo do arcabouço é permitir que agentes de IA consumam acervos volumosos (dezenas ou centenas de páginas) com **zero alucinação**, **máxima economia de tokens** e **recuperação cirúrgica** sem risco de estouro de contexto.

## Gatilhos da Skill (Triggers)

- **Comando:** `/add_reference`
- **Linguagem Natural:**
  - "Adicione como referência"
  - "Inclua como referência"
  - "Use isto como referência"
  - "Adicionar [arquivo] como referência"
  - "Cadastrar [documento] na base de conhecimento"
  - "Consultar catálogo de referências"

---

## Arquitetura em Pirâmide Multi-Tier

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

## Regras Invioláveis

1. **Limite Estrito de 450 Linhas por Arquivo Markdown:** Nenhum arquivo `.md` na pasta `.referencias` (inclusive partições do índice como `index_01.md`) deve ultrapassar 450 linhas. Se exceder, DEVE ser fatorado sequencialmente (`_01.md`, `_02.md`, etc.).
2. **Resumo Executivo Normativo Obrigatório (Tier 1):** Todo documento fatorado DEVE ter gerado automaticamente seu arquivo irmão `*_executive_brief.md` com limite estrito de **300 linhas**, contendo escopo, regras mandatórias (*"shall/must"*), entregáveis e a Matriz Léxica Remissiva.
3. **Particionamento Semântico Boundary-Aware:** A quebra de arquivos fatorados NUNCA deve ocorrer no meio de tabelas, blocos de código, listas ou parágrafos. A divisão deve respeitar os limites naturais de seções e títulos (`#`, `##`, `###`).
4. **Metadados em YAML Frontmatter:** Todo recorte fatorado DEVE conter cabeçalho YAML padronizado no topo com `document`, `part`, `total_parts`, `clauses`, `key_topics` e `upstream_references`.
5. **Eliminação Estrita de Marcadores de Página:** Tags como `<!-- Página X -->`, `<!-- Page X -->`, form feeds `\x0c` e rodapés/cabeçalhos de paginação (`Page X of Y`, marcas d'água de bibliotecas) são terminantemente proibidos no corpo dos arquivos Markdown finais.
6. **Fatoração do `index.md` (Índice Mestre):** Se o catálogo `index.md` ultrapassar 450 linhas, ele DEVE ser automaticamente transformado em um **Índice Mestre** contendo links para partições estruturadas (`index_01.md`, `index_02.md`, etc.), preservando cada partição abaixo do teto de 450 linhas.
7. **Idioma Padrão dos Documentos (`eng-US`):** Salvo solicitação explícita em contrário do usuário, todos os arquivos Markdown gerados na pasta `.referencias` devem adotar o idioma **English (US)** para máxima eficácia e economia de tokens dos LLMs. As respostas, explicações e interações com o usuário no chat permanecem estritamente em **Português do Brasil (pt-BR)**.
8. **Navegação Bidirecional e Links Relativos:** Em documentos fatorados, a Parte 01 contém o índice completo e todas as partes subsequentes contêm links relativos para a Parte 01 e para o Executive Brief.
9. **Arquivamento do Original:** Arquivos físicos originais (`.pdf`, `.xlsx`, `.docx`, etc.) devem ser movidos para `.referencias/docs_originais/` após a conversão.

---

## Protocolo de Recuperação para Agentes de IA (Zero-Overhead Retrieval)

Ao consumir referências na pasta `.referencias`, os agentes de IA do workspace DEVEM seguir o seguinte protocolo em 3 passos para não sobrecarregar a janela de contexto:

### Passo 1: Mapeamento Taxonômico (Tier 0)
- Leia apenas o arquivo `.referencias/index.md`.
- Identifique a referência relevante e verifique se há um `Executive Brief` disponível.

### Passo 2: Decisão e Extração de Regras (Tier 1)
- Abra o arquivo correspondente `*_executive_brief.md` (~1.000 a 1.500 tokens).
- Obtenha as **Regras Mandatórias ("Shall / Must")** e verifique na **Matriz Léxica** qual é a parte exata (`Part XX`) que trata do tópico em profundidade.
- Em mais de 80% das tomadas de decisão arquitetural, o `Executive Brief` é suficiente e elimina a necessidade de carregar o texto bruto.

### Passo 3: Consulta Cirúrgica Direta (Tier 2 ou CLI)
- **Opção A (Busca Via Terminal):** Execute o comando de busca cirúrgica para extrair apenas as linhas relevantes sem abrir o arquivo:
  - No Windows (PowerShell):
    ```powershell
    python "$HOME\.gemini\config\skills\add_reference\scripts\convert_to_md.py" --query "<termo ou cláusula>" "<workspace>/.referencias"
    ```
  - No Linux / macOS (Bash):
    ```bash
    python "$HOME/.gemini/config/skills/add_reference/scripts/convert_to_md.py" --query "<termo ou cláusula>" "<workspace>/.referencias"
    ```
  - Se instalado localmente no workspace (`.agents/skills/`):
    ```bash
    python ".agents/skills/add_reference/scripts/convert_to_md.py" --query "<termo ou cláusula>" "<workspace>/.referencias"
    ```
- **Opção B (Abertura Pontual):** Abra estritamente a parte apontada pela Matriz Léxica (ex: `view_file` em `nome_04.md`), evitando ler partes adjacentes desnecessárias.

---

## Fluxo de Execução Passo a Passo da Skill

### Passo 1: Identificação do Alvo
- Determine o artefato a ser processado (arquivo físico indicado no prompt, documento aberto no editor ou texto puro via stdin).

### Passo 2: Verificação da Estrutura de Pastas
Assegure que os seguintes diretórios existam na raiz do workspace ativo:
- `<workspace>/.referencias`
- `<workspace>/.referencias/docs_originais`

### Passo 3: Conversão, Fatoração e Atualização do Catálogo
Execute o script utilitário `convert_to_md.py` localizado na pasta `scripts/` da Skill:

- **Instalação Global no Windows (PowerShell):**
  ```powershell
  python "$HOME\.gemini\config\skills\add_reference\scripts\convert_to_md.py" "<caminho_do_arquivo_origem>" "<workspace>/.referencias" --lang "eng-US" --update-index
  ```
- **Instalação Global no Linux / macOS (Bash):**
  ```bash
  python "$HOME/.gemini/config/skills/add_reference/scripts/convert_to_md.py" "<caminho_do_arquivo_origem>" "<workspace>/.referencias" --lang "eng-US" --update-index
  ```
- **Instalação Local no Workspace:**
  ```bash
  python ".agents/skills/add_reference/scripts/convert_to_md.py" "<caminho_do_arquivo_origem>" "<workspace>/.referencias" --lang "eng-US" --update-index
  ```

*Nota para Bloco de Texto sem arquivo:* Passe o texto via stdin para o script usando `-` e os parâmetros `--name` e `--title`:
```powershell
Get-Content -Raw "temp_text.txt" | python "$HOME\.gemini\config\skills\add_reference\scripts\convert_to_md.py" - "<workspace>/.referencias" --name "<nome_snake_case>" --title "<Titulo Legivel>" --lang "eng-US" --update-index
```

### Passo 4: Leitura do Resultado
O script retornará um JSON estruturado com o status:
- `base_name`: Nome base gerado em `snake_case_down`.
- `title`: Título formal do artefato.
- `relative_main_file`: Caminho relativo para a Parte 01.
- `relative_executive_brief`: Caminho relativo para o Executive Brief gerado.
- `is_factored`: Boleano indicando se o arquivo ultrapassou 450 linhas e foi fatorado.
- `parts_count`: Quantidade de partes geradas.
- `parts_metadata`: Lista contendo número da parte, caminho relativo, cláusulas e tópicos temáticos.
- `index_action`: Ação executada no índice (`created`, `appended`, etc.).

### Passo 5: Arquivamento do Arquivo Original
- Mova o arquivo físico original para `<workspace>/.referencias/docs_originais/<nome_original_do_arquivo>`.

### Passo 6: Confirmação e Registro
Responda ao usuário em Português do Brasil (pt-BR) informando:
- O nome e título da referência cadastrada.
- Se houve fatoração e link para o `*_executive_brief.md` gerado.
- A quantidade de partes fatoradas com seus tópicos específicos.
- Confirmação de inclusão no `index.md` e arquivamento em `docs_originais/`.

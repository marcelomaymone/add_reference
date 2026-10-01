import os
import sys
import re
import json
import argparse
import subprocess
from pathlib import Path

def ensure_package(package_name, import_name=None):
    """Garante que um pacote Python esteja instalado silenciosamente."""
    if import_name is None:
        import_name = package_name
    try:
        __import__(import_name)
    except ImportError:
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install", package_name],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception as e:
            sys.stderr.write(f"Aviso: Não foi possível instalar {package_name}: {e}\n")

def to_snake_case_down(text):
    """Converte um texto para o padrão snake_case_down (letras minúsculas e underscores)."""
    text = Path(text).stem
    text = re.sub(r'[^\w\s-]', '', text).strip()
    text = re.sub(r'[\s-]+', '_', text)
    return text.lower()

def clean_markdown_content(text):
    """Realiza limpeza inteligente do conteúdo extraído, eliminando marcadores de página e marcas d'água."""
    # Remove form feeds
    text = text.replace('\x0c', '\n').replace('\f', '\n')
    
    # Remove tags HTML de comentário de página como <!-- Página X --> ou <!-- Page X -->
    text = re.sub(r'<!--\s*(?:Página|Page)\s*\d+\s*-->', '', text, flags=re.IGNORECASE)
    
    # Remove marcas d'água de bibliotecas digitais (ex: IEEE Xplore)
    text = re.sub(r'Authorized licensed use limited to:.*?(?:Restrictions apply\.?|$)', '', text, flags=re.IGNORECASE)
    
    # Remove glifos residuais de fontes de PDF (ex: /g127, /g0)
    text = re.sub(r'/g\d+\s*', '', text)
    
    # Regex para identificar linhas que são estritamente indicadores de página ou números isolados
    page_line_regex = re.compile(
        r'^\s*(?:[-–—]\s*)?(?:(?:Página|Page)\s*\d+(?:\s*(?:de|of|/)\s*\d+)?|\d+\s*(?:de|of|/)\s*\d+|(?:Página|Page)\s*\d+|\d{1,4})\s*(?:[-–—]\s*)?$',
        re.IGNORECASE
    )
    
    # Captura rodapés e cabeçalhos com referências a normas e números de página
    doc_page_footer_regex = re.compile(
        r'^\s*(?:ISO|IEC|IEEE|ABNT|NBR|RFC).*\b(?:Page|Página)\s*\d+\s*$',
        re.IGNORECASE
    )
    
    lines = text.splitlines()
    cleaned = []
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append("")
            continue
        # Limpa número de página colado no final de linhas de copyright (ex: "© IEEE 2011 – All rights reserved 63")
        stripped_copyright = re.sub(r'(©\s*(?:ISO|IEC|IEEE|ABNT)[^–—\n]+[–—]\s*All rights reserved)\s+\d{1,4}\s*$', r'\1', stripped, flags=re.IGNORECASE)
        if stripped_copyright != stripped:
            stripped = stripped_copyright
            line = stripped_copyright
            
        if page_line_regex.match(stripped) or doc_page_footer_regex.match(stripped):
            continue
        cleaned.append(line)
        
    result = "\n".join(cleaned)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()

def convert_pdf(file_path):
    """Extrai conteúdo de arquivo PDF sem marcadores de página."""
    ensure_package("pypdf")
    import pypdf
    
    text_content = []
    reader = pypdf.PdfReader(file_path)
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_content.append(page_text)
    return "\n\n".join(text_content)

def convert_docx(file_path):
    """Extrai conteúdo de arquivo DOCX."""
    ensure_package("python-docx", "docx")
    import docx
    
    doc = docx.Document(file_path)
    md_lines = []
    
    for p in doc.paragraphs:
        style_name = p.style.name.lower() if p.style else ""
        text = p.text.strip()
        if not text:
            continue
            
        if "heading 1" in style_name:
            md_lines.append(f"# {text}")
        elif "heading 2" in style_name:
            md_lines.append(f"## {text}")
        elif "heading 3" in style_name:
            md_lines.append(f"### {text}")
        elif "heading 4" in style_name or "heading 5" in style_name:
            md_lines.append(f"#### {text}")
        else:
            md_lines.append(text)
            
    for table in doc.tables:
        md_lines.append("\n")
        headers = [cell.text.strip() for cell in table.rows[0].cells]
        md_lines.append("| " + " | ".join(headers) + " |")
        md_lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
        for row in table.rows[1:]:
            row_vals = [cell.text.strip() for cell in row.cells]
            md_lines.append("| " + " | ".join(row_vals) + " |")
        md_lines.append("\n")
        
    return "\n".join(md_lines)

def convert_excel(file_path):
    """Extrai conteúdo de planilhas Excel (.xlsx, .xls)."""
    ensure_package("pandas")
    ensure_package("openpyxl")
    ensure_package("tabulate")
    import pandas as pd
    
    excel_file = pd.ExcelFile(file_path)
    md_sections = []
    
    for sheet_name in excel_file.sheet_names:
        df = pd.read_excel(excel_file, sheet_name=sheet_name)
        if df.empty:
            continue
        md_sections.append(f"## Aba: {sheet_name}\n")
        md_table = df.to_markdown(index=False)
        md_sections.append(md_table)
        md_sections.append("\n")
        
    return "\n".join(md_sections)

def convert_csv(file_path):
    """Extrai conteúdo de arquivos CSV."""
    ensure_package("pandas")
    ensure_package("tabulate")
    import pandas as pd
    
    try:
        df = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(file_path, encoding='latin1')
        
    return df.to_markdown(index=False)

def convert_pptx(file_path):
    """Extrai conteúdo de apresentações PowerPoint (.pptx)."""
    ensure_package("python-pptx", "pptx")
    from pptx import Presentation
    
    prs = Presentation(file_path)
    md_lines = []
    
    for idx, slide in enumerate(prs.slides):
        md_lines.append(f"## Slide {idx+1}")
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                md_lines.append(shape.text.strip())
        md_lines.append("\n---")
        
    return "\n".join(md_lines)

def convert_text(file_path):
    """Lê arquivos de texto puro ou markdown."""
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    raise ValueError(f"Não foi possível ler o arquivo {file_path} com os encodigs suportados.")

def extract_file_content(file_path):
    """Determina o parser apropriado com base na extensão."""
    ext = Path(file_path).suffix.lower()
    
    if ext == '.pdf':
        return convert_pdf(file_path)
    elif ext in ['.docx', '.doc']:
        return convert_docx(file_path)
    elif ext in ['.xlsx', '.xls']:
        return convert_excel(file_path)
    elif ext == '.csv':
        return convert_csv(file_path)
    elif ext == '.pptx':
        return convert_pptx(file_path)
    else:
        return convert_text(file_path)

def generate_summary(text, max_words=40):
    """Gera uma ementa/síntese concisa e informativa do documento extraído."""
    scope_match = re.search(r'(?:1\s+Scope|Clause 1\s+Scope|1\.\s+Scope)\s*\n+([^\n]+(?:\n+[^\n]+)?)', text, re.IGNORECASE)
    if scope_match:
        scope_text = " ".join(scope_match.group(1).split())
        words = scope_text.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return scope_text
        
    meta_prefixes = ["reference number", "international standard", "iso/", "ieee", "©", "first edition", "second edition"]
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.startswith('#')]
    informative_lines = [
        l for l in lines 
        if not any(l.lower().startswith(p) for p in meta_prefixes) and len(l) > 15
    ]
    if informative_lines:
        first_para = informative_lines[0]
        words = first_para.split()
        if len(words) > max_words:
            return " ".join(words[:max_words]) + "..."
        return first_para
    return "Technical reference document."

def extract_chunk_topics_list(chunk, lang="eng-US", max_topics=4):
    """Retorna uma lista de strings com os títulos ou cláusulas do recorte."""
    topics = []
    seen = set()
    
    # 1. Busca por cabeçalhos Markdown (#, ##, ###, ####)
    header_pattern = re.compile(r'^(#{1,4})\s+(.+)$', re.MULTILINE)
    for match in header_pattern.finditer(chunk):
        h_text = match.group(2).strip()
        if any(ign in h_text.lower() for ign in ["navigation", "navegação", "factored document index", "índice do documento"]):
            continue
        h_clean = re.sub(r'[*_`]', '', h_text).strip()
        if len(h_clean) > 75:
            h_clean = h_clean[:72] + "..."
        if h_clean and h_clean.lower() not in seen:
            topics.append(h_clean)
            seen.add(h_clean.lower())
        if len(topics) >= max_topics:
            break
            
    # 2. Busca por anexos formais (ex: Annex A, Annex D)
    if len(topics) < max_topics:
        annex_pattern = re.compile(r'^\s*(?:Annex|Apêndice)\s+([A-Z]\b[^\n]*)', re.MULTILINE | re.IGNORECASE)
        for match in annex_pattern.finditer(chunk):
            annex_str = f"Annex {match.group(1).strip()}"
            if annex_str.lower() not in seen:
                topics.append(annex_str)
                seen.add(annex_str.lower())
            if len(topics) >= max_topics:
                break

    # 3. Busca por cláusulas/seções normativas numeradas (ex: 5.2 Stakeholders, A.2 OpsCon, D.1 Introduction)
    if len(topics) < max_topics:
        clause_pattern = re.compile(
            r'^\s*(?:Clause|Section|Cláusula|Seção)?\s*([A-Za-z0-9]+(?:\.[0-9]+)+\s+[A-Z][A-Za-z0-9\s,–—\-_/()]+)',
            re.MULTILINE
        )
        for match in clause_pattern.finditer(chunk):
            c_text = match.group(1).strip()
            c_first_line = c_text.splitlines()[0].strip()
            if len(c_first_line) > 75:
                c_first_line = c_first_line[:72] + "..."
            if c_first_line and c_first_line.lower() not in seen:
                topics.append(c_first_line)
                seen.add(c_first_line.lower())
            if len(topics) >= max_topics:
                break

    # 4. Busca por seções formais de aviso/metadados
    if len(topics) < max_topics:
        notice_pattern = re.compile(
            r'^\s*(Abstract|Important Notice|Interpretations|Patents|Copyrights|Laws and regulations|Updating of IEEE documents)\b',
            re.MULTILINE | re.IGNORECASE
        )
        for match in notice_pattern.finditer(chunk):
            n_text = match.group(1).title()
            if n_text.lower() not in seen:
                topics.append(n_text)
                seen.add(n_text.lower())
            if len(topics) >= max_topics:
                break

    cleaned_topics = []
    for t in topics:
        t_clean = re.sub(r'\s*\.{3,}\s*\d*', '', t)
        t_clean = re.sub(r'\s{2,}', ' ', t_clean).strip()
        if t_clean:
            cleaned_topics.append(t_clean)
            
    if not cleaned_topics:
        fallback = generate_summary(chunk, max_words=15)
        if fallback and not fallback.startswith("#"):
            cleaned_topics.append(fallback)
        else:
            cleaned_topics.append("Technical content and specifications" if lang == "eng-US" else "Conteúdo técnico")
            
    return cleaned_topics

def extract_chunk_topics(chunk, lang="eng-US", max_topics=4):
    """Extrai títulos, cláusulas ou tópicos-chave de um recorte de texto como string unificada."""
    topics = extract_chunk_topics_list(chunk, lang=lang, max_topics=max_topics)
    return ", ".join(topics)

def extract_chunk_clauses(chunk):
    """Extrai lista concisa de cláusulas/seções para o YAML Frontmatter."""
    clauses = []
    seen = set()
    pat = re.compile(r'^\s*(?:Clause|Section|Annex)?\s*([A-Za-z0-9]+(?:\.[0-9]+)+|[A-Z]\.\d+|Annex\s+[A-Z])\b', re.MULTILINE | re.IGNORECASE)
    for m in pat.finditer(chunk):
        c = m.group(1).strip()
        if c.lower() not in seen and len(c) <= 18:
            clauses.append(c)
            seen.add(c.lower())
        if len(clauses) >= 6:
            break
    return clauses

def build_yaml_frontmatter(base_name, part_num, total_parts, clauses, topics, upstream_refs):
    """Gera o cabeçalho estruturado YAML Frontmatter para cada parte."""
    lines = [
        "---",
        f"document: \"{base_name}\"",
        f"part: {part_num}",
        f"total_parts: {total_parts}",
        f"clauses: {json.dumps(clauses, ensure_ascii=False)}",
        f"key_topics: {json.dumps(topics, ensure_ascii=False)}",
        "upstream_references:"
    ]
    for ref in upstream_refs:
        lines.append(f"  - \"{ref}\"")
    lines.append("---\n\n")
    return "\n".join(lines)

def split_boundary_aware(content, max_lines=450, chunk1_reserve=60, other_reserve=40):
    """Divide o conteúdo respeitando limites de seções, tabelas e blocos lógicos."""
    lines = content.splitlines()
    total_lines = len(lines)
    
    if total_lines <= (max_lines - 10):
        return [content]
        
    blocks = []
    current_block = []
    in_table = False
    in_code = False
    
    for line in lines:
        stripped = line.strip()
        is_heading = bool(re.match(r'^#{1,4}\s+', stripped))
        is_table_row = stripped.startswith('|')
        is_code_fence = stripped.startswith('```')
        
        if is_code_fence:
            in_code = not in_code
            
        if is_table_row and not in_table:
            in_table = True
        elif in_table and not is_table_row and stripped != "":
            in_table = False
            
        if not in_code and not in_table:
            if is_heading and current_block:
                blocks.append("\n".join(current_block))
                current_block = [line]
                continue
            elif stripped == "" and current_block:
                current_block.append(line)
                blocks.append("\n".join(current_block))
                current_block = []
                continue
                
        current_block.append(line)
        
    if current_block:
        blocks.append("\n".join(current_block))
        
    chunks = []
    current_chunk = []
    current_target_limit = max_lines - chunk1_reserve
    
    for block in blocks:
        block_lines = len(block.splitlines())
        if block_lines > current_target_limit:
            if current_chunk:
                chunks.append("\n".join(current_chunk).strip())
                current_chunk = []
                current_target_limit = max_lines - other_reserve
            b_lines = block.splitlines()
            for i in range(0, len(b_lines), current_target_limit):
                slice_b = "\n".join(b_lines[i:i + current_target_limit])
                if i + current_target_limit < len(b_lines):
                    chunks.append(slice_b.strip())
                else:
                    current_chunk = [slice_b]
            continue
            
        test_chunk = current_chunk + [block]
        test_lines = len("\n".join(test_chunk).splitlines())
        if test_lines > current_target_limit and current_chunk:
            chunks.append("\n".join(current_chunk).strip())
            current_chunk = [block]
            current_target_limit = max_lines - other_reserve
        else:
            current_chunk.append(block)
            
    if current_chunk:
        chunks.append("\n".join(current_chunk).strip())
        
    return chunks

def generate_executive_brief(content, base_name, title, parts_metadata, lang="eng-US"):
    """Gera o Resumo Executivo Normativo (Tier 1) com regras mandatórias, léxico e protocolo de retrieval."""
    num_parts = len(parts_metadata)
    doc_title = title or base_name.replace('_', ' ').title()
    
    # 1. Escopo e Objetivo
    scope_text = generate_summary(content, max_words=60)
    
    # 2. Extração de Regras Mandatórias ("shall / must")
    mandatory_rules = []
    seen_rules = set()
    
    # Termos e disclaimers administrativos/editoriais a desconsiderar
    ignore_editorial_terms = [
        "typeface", "typefaces", "embedded", "copyright", "photocopying", 
        "permission", "licensee", "liability", "disclaimer", "iso copyright office",
        "inhabitant", "adobe systems", "electronic retrieval", "published in switzerland"
    ]
    
    lines = content.splitlines()
    current_clause = "General Requirements"
    
    for line in lines:
        stripped = line.strip()
        clause_match = re.match(r'^(?:#+\s*)?(?:Clause|Section)?\s*([A-Za-z0-9]+(?:\.[0-9]+)+|[A-Z]\.\d+)\s+([A-Za-z0-9\s,–—\-_/()]+)', stripped)
        if clause_match:
            current_clause = f"Clause {clause_match.group(1)} ({clause_match.group(2).strip()})"
            if len(current_clause) > 55:
                current_clause = current_clause[:52] + "..."
            continue
            
        stripped_lower = stripped.lower()
        if "shall" in stripped_lower or "must" in stripped_lower:
            if any(term in stripped_lower for term in ignore_editorial_terms):
                continue
            sentences = re.split(r'\.\s+', stripped)
            for s in sentences:
                s_lower = s.lower()
                if ("shall" in s_lower or "must" in s_lower) and not any(term in s_lower for term in ignore_editorial_terms):
                    s_clean = s.strip().rstrip('.')
                    s_clean = re.sub(r'^[-–—*•\s]+', '', s_clean)
                    s_clean = re.sub(r'^/g\d+\s*', '', s_clean)
                    if len(s_clean) > 20 and len(s_clean) < 180 and s_clean.lower() not in seen_rules:
                        mandatory_rules.append((current_clause, s_clean))
                        seen_rules.add(s_clean.lower())
                if len(mandatory_rules) >= 12:
                    break
        if len(mandatory_rules) >= 12:
            break
            
    # 3. Matriz Léxica Remissiva com conceitos-chave
    core_concepts = [
        ("SyRS", "System Requirements Specification", [r'\bSyRS\b', r'System Requirements Specification']),
        ("StRS", "Stakeholder Requirements Specification", [r'\bStRS\b', r'Stakeholder Requirements Specification']),
        ("OpsCon", "System Operational Concept Document", [r'\bOpsCon\b', r'Operational Concept']),
        ("ConOps", "Concept of Operations Document", [r'\bConOps\b', r'Concept of Operations']),
        ("ICD", "Interface Control Document & Boundaries", [r'\bICD\b', r'Interface Control Document', r'Interface Requirements']),
        ("Verification", "Requirements Verification Process and Criteria", [r'Verification Process', r'Requirement Verification', r'Verification Criteria', r'\bVerification\b']),
        ("Validation", "Requirements Validation Process", [r'Validation Process', r'Requirement Validation', r'\bValidation\b']),
        ("Stakeholders", "Stakeholder Identification and Requirements Elicitation", [r'Stakeholder Identification', r'Stakeholder Requirements Definition Process', r'\bStakeholder\b']),
        ("Architecture", "System Architecture Allocation and Synthesis", [r'Architecture Design Process', r'Architecture Definition', r'Allocation', r'\bArchitecture\b']),
        ("Tailoring", "Tailoring Policies and Standards Conformance", [r'\bTailoring\b', r'Annex D\b'])
    ]
    
    lexicon_matrix = []
    for item in core_concepts:
        term = item[0]
        desc = item[1]
        patterns = item[2] if len(item) > 2 else [rf'\b{re.escape(term)}\b']
        
        part_scores = []
        for p_meta in parts_metadata:
            p_num = p_meta["part_number"]
            chunk_text = p_meta.get("content", "")
            topics_text = " ".join(p_meta.get("topics_list", []))
            clauses_text = " ".join(p_meta.get("clauses_list", []))
            
            score = 0
            
            is_defs = any("terms and definition" in t.lower() for t in p_meta.get("topics_list", [])) or "terms and definition" in chunk_text[:300].lower()
            if p_num == 1:
                score -= 40
            if is_defs:
                score -= 25
                
            for pat in patterns:
                h_matches = len(re.findall(rf'^(?:#{{1,4}})\s+.*(?:{pat}).*$', chunk_text, re.MULTILINE | re.IGNORECASE))
                score += h_matches * 80
                
                t_matches = len(re.findall(pat, topics_text, re.IGNORECASE))
                score += t_matches * 40
                c_matches = len(re.findall(pat, clauses_text, re.IGNORECASE))
                score += c_matches * 30
                
                body_matches = len(re.findall(pat, chunk_text, re.IGNORECASE))
                score += min(body_matches * 4, 60)
                
            part_scores.append((score, p_meta))
            
        part_scores.sort(key=lambda x: x[0], reverse=True)
        
        if part_scores and part_scores[0][0] > 0:
            top_score, top_meta = part_scores[0]
            recommended_parts = [top_meta]
            
            if len(part_scores) > 1 and part_scores[1][0] >= 40 and (part_scores[1][0] >= top_score * 0.6):
                second_score, second_meta = part_scores[1]
                recommended_parts = sorted([top_meta, second_meta], key=lambda x: x["part_number"])
                
            links_str = ", ".join([f"[Part {pm['part_number']:02d}]({pm['relative_path']})" for pm in recommended_parts])
            lexicon_matrix.append((term, desc, links_str))
        else:
            lexicon_matrix.append((term, desc, f"[Part 01](./{base_name}_01.md)"))

    out = []
    out.append(f"# {doc_title} - Executive Brief & Normative Core\n")
    out.append(f"> **Document Family:** `{base_name}` | **Factored Parts:** {num_parts}")
    out.append("> **Tier:** 1 (Executive Summary, Normative Mandates & Lexicon Matrix)\n")
    out.append("---\n")
    
    out.append("## Agent Fast Retrieval Protocol")
    out.append("1. **Zero-Overhead Decision Making:** Consult the Mandatory Rules below before reading deep text parts.")
    out.append("2. **Surgical Deep Dives:** Use the Lexicon Matrix below to navigate directly to the specific factored part.")
    out.append("3. **CLI Precision Search:** Execute `python convert_to_md.py --query \"<term>\" <dir>` for exact clause snippets with line numbers.\n")
    out.append("---\n")
    
    out.append("## 1. Scope & Primary Objectives")
    out.append(f"{scope_text}\n")
    
    out.append("## 2. Core Mandatory Rules ('Shall / Must' Principles)")
    if mandatory_rules:
        for clause, rule in mandatory_rules:
            out.append(f"*   **[{clause}]:** {rule}.")
    else:
        out.append("*   All processes and requirements engineering activities defined in this standard must be verified against stakeholder criteria.")
    out.append("")
    
    out.append("## 3. Key Deliverables & Process Artifacts")
    out.append("| Artifact | Purpose | Primary Focus |")
    out.append("| --- | --- | --- |")
    out.append("| **StRS** | Stakeholder Requirements Specification | User needs, operating concepts, constraints |")
    out.append("| **SyRS** | System Requirements Specification | Technical system functions, interfaces, verification |")
    out.append("| **OpsCon** | Operational Concept Document | Operational scenarios, modes, user classes |")
    out.append("| **ICD** | Interface Control Document | Internal and external system boundaries |\n")
    
    out.append("## 4. Lexicon & Terminology Mapping Matrix")
    out.append("| Term / Concept | Description | Target Factored Part |")
    out.append("| --- | --- | --- |")
    for term, desc, part_link in lexicon_matrix:
        out.append(f"| **{term}** | {desc} | {part_link} |")
    out.append("")
    
    brief_content = "\n".join(out).strip() + "\n"
    
    brief_lines = brief_content.splitlines()
    if len(brief_lines) > 300:
        brief_content = "\n".join(brief_lines[:298]) + "\n\n*(Truncated to comply with strict 300-line executive limit)*\n"
    return brief_content

def split_and_save_markdown(content, target_dir, base_name, max_lines=450, lang="eng-US"):
    """Divide o conteúdo com particionamento boundary-aware, frontmatter YAML e gera executive brief."""
    target_path = Path(target_dir)
    target_path.mkdir(parents=True, exist_ok=True)
    doc_title = base_name.replace('_', ' ').title()
    
    lines = content.splitlines()
    total_lines = len(lines)
    
    if total_lines <= max_lines:
        file_name = f"{base_name}.md"
        full_path = target_path / file_name
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "is_factored": False,
            "parts_count": 1,
            "files": [str(full_path)],
            "main_file": str(full_path),
            "relative_main_file": f"./{file_name}",
            "parts_metadata": [
                {
                    "part_number": 1,
                    "file_name": file_name,
                    "relative_path": f"./{file_name}",
                    "topics_summary": extract_chunk_topics(content, lang=lang)
                }
            ]
        }
        
    # Fatoração Boundary-Aware
    chunks = split_boundary_aware(content, max_lines=max_lines, chunk1_reserve=60, other_reserve=40)
    num_parts = len(chunks)
    
    # Extração de Metadados de cada parte
    parts_metadata = []
    for idx, chunk in enumerate(chunks):
        p_num = idx + 1
        part_filename = f"{base_name}_{p_num:02d}.md"
        p_file_rel = f"./{part_filename}"
        topics_str = extract_chunk_topics(chunk, lang=lang)
        clauses_list = extract_chunk_clauses(chunk)
        topics_list = extract_chunk_topics_list(chunk, lang=lang)
        
        parts_metadata.append({
            "part_number": p_num,
            "file_name": part_filename,
            "relative_path": p_file_rel,
            "topics_summary": topics_str,
            "topics_list": topics_list,
            "clauses_list": clauses_list,
            "content": chunk
        })
        
    # 1. Gera o Executive Brief (Tier 1)
    brief_content = generate_executive_brief(content, base_name, doc_title, parts_metadata, lang=lang)
    brief_filename = f"{base_name}_executive_brief.md"
    brief_full_path = target_path / brief_filename
    brief_rel_path = f"./{brief_filename}"
    brief_full_path.write_text(brief_content, encoding='utf-8')
    
    main_file_rel = f"./{base_name}_01.md"
    created_files = []
    
    # 2. Salva cada parte com YAML Frontmatter e Navegação
    for idx, chunk in enumerate(chunks):
        p_num = idx + 1
        p_meta = parts_metadata[idx]
        part_filename = p_meta["file_name"]
        part_full_path = target_path / part_filename
        
        upstream_refs = [main_file_rel, brief_rel_path]
        yaml_front = build_yaml_frontmatter(
            base_name=base_name,
            part_num=p_num,
            total_parts=num_parts,
            clauses=p_meta["clauses_list"],
            topics=p_meta["topics_list"],
            upstream_refs=upstream_refs
        )
        
        if lang == "eng-US":
            nav_bar = f"> **Navigation:** [← Return to Factored Document Index (Part 01)]({main_file_rel}) | [Executive Brief]({brief_rel_path}) | **Part {p_num} of {num_parts}**\n\n---\n\n"
        else:
            nav_bar = f"> **Navegação:** [← Voltar para Índice do Documento (Parte 01)]({main_file_rel}) | [Resumo Executivo]({brief_rel_path}) | **Parte {p_num} de {num_parts}**\n\n---\n\n"
            
        if p_num == 1:
            if lang == "eng-US":
                index_sec = f"# {doc_title}\n\n"
                index_sec += "## Factored Document Index\n\n"
                index_sec += f"This document has been factored into **{num_parts} parts** (respecting the strict limit of {max_lines} lines per file):\n\n"
                index_sec += f"*   **[Executive Brief & Normative Core]({brief_rel_path}):** Mandates, key principles and lexicon matrix (< 300 lines)\n"
                for pm in parts_metadata:
                    index_sec += f"*   **[Part {pm['part_number']:02d}]({pm['relative_path']}):** {pm['topics_summary']}\n"
                index_sec += "\n---\n\n"
            else:
                index_sec = f"# {doc_title}\n\n"
                index_sec += "## Índice do Documento Fatorado\n\n"
                index_sec += f"Este documento foi fatorado em **{num_parts} partes** (respeitando o limite estrito de {max_lines} linhas por arquivo):\n\n"
                index_sec += f"*   **[Resumo Executivo & Regras Mandatórias]({brief_rel_path}):** Mandatos, princípios e matriz léxica (< 300 linhas)\n"
                for pm in parts_metadata:
                    index_sec += f"*   **[Parte {pm['part_number']:02d}]({pm['relative_path']}):** {pm['topics_summary']}\n"
                index_sec += "\n---\n\n"
                
            final_content = yaml_front + index_sec + chunk
        else:
            final_content = yaml_front + nav_bar + chunk
            
        part_full_path.write_text(final_content, encoding='utf-8')
        created_files.append(str(part_full_path))
        
    clean_parts_meta = []
    for pm in parts_metadata:
        pm_copy = dict(pm)
        pm_copy.pop("content", None)
        clean_parts_meta.append(pm_copy)
        
    return {
        "is_factored": True,
        "parts_count": num_parts,
        "files": created_files,
        "main_file": created_files[0],
        "relative_main_file": main_file_rel,
        "parts_metadata": clean_parts_meta,
        "executive_brief_file": str(brief_full_path),
        "relative_executive_brief": brief_rel_path
    }

def format_index_entry(entry_data, lang="eng-US"):
    """Formata uma entrada individual para o catálogo de referências index.md."""
    title = entry_data.get("title", "Document")
    summary = entry_data.get("summary", "")
    rel_main = entry_data.get("relative_main_file", "")
    rel_brief = entry_data.get("relative_executive_brief", "")
    is_factored = entry_data.get("is_factored", False)
    parts_meta = entry_data.get("parts_metadata", [])
    
    if lang == "eng-US":
        lines = [f"### {title}"]
        if rel_brief:
            lines.append(f"*   **Executive Brief:** [{rel_brief}]({rel_brief}) (Mandatory rules & lexicon)")
        lines.append(f"*   **Summary:** {summary}")
        lines.append(f"*   **Full Reference:** [{rel_main}]({rel_main})")
        if is_factored and parts_meta:
            lines.append("*   **Factored Parts & Topics:**")
            for p in parts_meta:
                lines.append(f"    *   **[Part {p['part_number']:02d}]({p['relative_path']}):** {p['topics_summary']}")
    else:
        lines = [f"### {title}"]
        if rel_brief:
            lines.append(f"*   **Resumo Executivo:** [{rel_brief}]({rel_brief}) (Regras mandatórias e léxico)")
        lines.append(f"*   **Ementa:** {summary}")
        lines.append(f"*   **Referência Completa:** [{rel_main}]({rel_main})")
        if is_factored and parts_meta:
            lines.append("*   **Partes Fatoradas & Ementas:**")
            for p in parts_meta:
                lines.append(f"    *   **[Parte {p['part_number']:02d}]({p['relative_path']}):** {p['topics_summary']}")
                
    return "\n".join(lines) + "\n\n"

def update_or_split_index(index_path, entry_data, max_lines=450, lang="eng-US"):
    """Insere novas referências e gerencia a fatoração em Índice Mestre e partições quando > max_lines."""
    index_file = Path(index_path)
    target_dir = index_file.parent
    target_dir.mkdir(parents=True, exist_ok=True)
    
    entry_text = format_index_entry(entry_data, lang=lang)
    entry_lines_count = len(entry_text.splitlines())
    
    if not index_file.exists():
        if lang == "eng-US":
            init_header = (
                "# Workspace Reference Index\n\n"
                "Normative and technical references cataloged by AI Knowledge Librarian.\n\n"
                "---\n\n"
            )
        else:
            init_header = (
                "# Índice Central de Referências do Workspace\n\n"
                "Base normativo-documental catalogada pelo Agente AI Knowledge Librarian.\n\n"
                "---\n\n"
            )
        total_content = init_header + entry_text
        index_file.write_text(total_content, encoding="utf-8")
        return {"action": "created", "file": str(index_file)}
        
    current_content = index_file.read_text(encoding="utf-8")
    is_master = ("Master Reference Index" in current_content) or ("Índice Mestre de Referências" in current_content)
    
    if is_master:
        partition_files = sorted(target_dir.glob("index_[0-9][0-9].md"))
        if not partition_files:
            latest_num = 1
            latest_part_file = target_dir / "index_01.md"
        else:
            latest_part_file = partition_files[-1]
            latest_num = int(latest_part_file.stem.split("_")[1])
            
        part_content = latest_part_file.read_text(encoding="utf-8") if latest_part_file.exists() else ""
        part_lines = len(part_content.splitlines())
        
        if (part_lines + entry_lines_count) <= max_lines and latest_part_file.exists():
            new_part_content = part_content.rstrip() + "\n\n" + entry_text
            latest_part_file.write_text(new_part_content, encoding="utf-8")
            return {"action": "appended_to_partition", "file": str(latest_part_file)}
        else:
            next_num = latest_num + 1 if latest_part_file.exists() else latest_num
            next_part_file = target_dir / f"index_{next_num:02d}.md"
            if lang == "eng-US":
                part_header = (
                    f"# Reference Index Partition {next_num:02d}\n\n"
                    f"> **Navigation:** [← Return to Master Index](./index.md)\n\n"
                    "---\n\n"
                )
            else:
                part_header = (
                    f"# Partição {next_num:02d} do Índice de Referências\n\n"
                    f"> **Navegação:** [← Voltar ao Índice Mestre](./index.md)\n\n"
                    "---\n\n"
                )
            next_part_file.write_text(part_header + entry_text, encoding="utf-8")
            
            part_rel = f"./index_{next_num:02d}.md"
            if lang == "eng-US":
                master_link = f"*   **[Index Part {next_num:02d}]({part_rel}):** Normative catalog partition {next_num:02d}\n"
            else:
                master_link = f"*   **[Partição {next_num:02d}]({part_rel}):** Catálogo normativo partição {next_num:02d}\n"
                
            index_file.write_text(current_content.rstrip() + "\n" + master_link, encoding="utf-8")
            return {"action": "created_new_partition", "file": str(next_part_file)}

    current_lines = len(current_content.splitlines())
    if (current_lines + entry_lines_count) <= max_lines:
        updated_content = current_content.rstrip() + "\n\n" + entry_text
        index_file.write_text(updated_content, encoding="utf-8")
        return {"action": "appended", "file": str(index_file)}
        
    # Transbordo para Índice Mestre
    part1_file = target_dir / "index_01.md"
    if lang == "eng-US":
        part1_header = (
            "# Reference Index Partition 01\n\n"
            "> **Navigation:** [← Return to Master Index](./index.md)\n\n"
            "---\n\n"
        )
    else:
        part1_header = (
            "# Partição 01 do Índice de Referências\n\n"
            "> **Navegação:** [← Voltar ao Índice Mestre](./index.md)\n\n"
            "---\n\n"
        )
        
    existing_entries = current_content
    for marker in ["---", "# Workspace Reference Index", "# Índice Central"]:
        if marker in existing_entries:
            idx = existing_entries.find("---")
            if idx != -1:
                existing_entries = existing_entries[idx+3:].strip()
                break
                
    part1_content = part1_header + existing_entries + "\n\n" + entry_text
    part1_file.write_text(part1_content, encoding="utf-8")
    
    if lang == "eng-US":
        master_content = (
            "# Master Reference Index\n\n"
            "Workspace knowledge catalog managed by AI Knowledge Librarian.\n"
            "Due to catalog volume, detailed references are partitioned below:\n\n"
            "---\n\n"
            "## Partitions\n\n"
            "*   **[Index Part 01](./index_01.md):** Initial partition of cataloged references\n"
        )
    else:
        master_content = (
            "# Índice Mestre de Referências do Workspace\n\n"
            "Catálogo de conhecimento do workspace gerenciado pelo AI Knowledge Librarian.\n"
            "Devido ao volume do acervo, as referências detalhadas estão particionadas abaixo:\n\n"
            "---\n\n"
            "## Partições\n\n"
            "*   **[Partição 01](./index_01.md):** Partição inicial de referências catalogadas\n"
        )
    index_file.write_text(master_content, encoding="utf-8")
    return {"action": "factored_to_master", "file": str(index_file), "partition": str(part1_file)}

def search_reference_catalog(catalog_dir, query_term, max_results=3):
    """Realiza busca cirúrgica textual nos arquivos Markdown do catálogo sem exigir leitura completa."""
    results = []
    target_path = Path(catalog_dir)
    if not target_path.exists():
        return results
        
    query_lower = query_term.lower().strip()
    query_words = [w for w in re.split(r'\s+', query_lower) if len(w) > 2]
    
    md_files = sorted(target_path.glob("*.md"))
    
    for f in md_files:
        # Pula arquivos de índice para focar no conteúdo normativo
        if f.name.startswith("index"):
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception:
            continue
            
        lines = content.splitlines()
        for idx, line in enumerate(lines):
            line_lower = line.lower()
            # Match exato ou todos os termos principais presentes na linha ou linhas adjacentes
            if query_lower in line_lower or (query_words and all(w in line_lower for w in query_words)):
                start_line = max(0, idx - 2)
                end_line = min(len(lines), idx + 18)
                snippet_lines = lines[start_line:end_line]
                snippet_text = "\n".join(snippet_lines).strip()
                
                results.append({
                    "file": str(f),
                    "file_name": f.name,
                    "relative_file": f"./{f.name}",
                    "line_start": start_line + 1,
                    "line_end": end_line,
                    "snippet": snippet_text
                })
                if len(results) >= max_results:
                    break
        if len(results) >= max_results:
            break
            
    return results

def main():
    parser = argparse.ArgumentParser(description="Utilitário de conversão, fatoração e busca para a skill /add_reference")
    parser.add_argument("source", nargs="?", default=None, help="Caminho do arquivo de origem, diretório de busca ou '-' para stdin")
    parser.add_argument("target_dir", nargs="?", default=None, help="Diretório de destino (.referencias)")
    parser.add_argument("--query", help="Executa busca cirúrgica textual no catálogo de referências")
    parser.add_argument("--name", help="Nome personalizado do arquivo (snake_case_down)")
    parser.add_argument("--title", help="Título amigável para exibição no índice")
    parser.add_argument("--max-lines", type=int, default=450, help="Limite de linhas para fatoração")
    parser.add_argument("--lang", default="eng-US", choices=["eng-US", "pt-BR"], help="Idioma padrão dos artefatos gerados")
    parser.add_argument("--update-index", action="store_true", help="Atualiza ou fatore automaticamente o index.md")
    
    args = parser.parse_args()
    
    # Modo de Busca Cirúrgica
    if args.query:
        search_dir = args.source or args.target_dir or "."
        matches = search_reference_catalog(search_dir, args.query)
        if not matches:
            print(f"Nenhuma ocorrência encontrada para: '{args.query}' em {search_dir}")
            sys.exit(0)
            
        print(f"### Search Results for: \"{args.query}\" (Found {len(matches)} matches)\n")
        for i, m in enumerate(matches, 1):
            print(f"#### Match {i}: `{m['relative_file']}` (Lines {m['line_start']}-{m['line_end']})")
            print("```markdown")
            print(m["snippet"])
            print("```\n")
        sys.exit(0)
        
    if not args.source or not args.target_dir:
        parser.print_help()
        sys.exit(1)
        
    try:
        if args.source == '-':
            content = sys.stdin.read()
            base_name = args.name or "referencia_texto"
            is_text_input = True
        else:
            source_path = Path(args.source).resolve()
            if not source_path.exists():
                raise FileNotFoundError(f"Arquivo não encontrado: {source_path}")
            content = extract_file_content(str(source_path))
            base_name = args.name or to_snake_case_down(source_path.name)
            is_text_input = False
            
        cleaned_content = clean_markdown_content(content)
        summary = generate_summary(cleaned_content)
        
        save_result = split_and_save_markdown(
            cleaned_content,
            args.target_dir,
            base_name,
            max_lines=args.max_lines,
            lang=args.lang
        )
        
        doc_title = args.title or base_name.replace('_', ' ').title()
        
        index_result = None
        if args.update_index:
            index_path = Path(args.target_dir) / "index.md"
            entry_data = {
                "title": doc_title,
                "summary": summary,
                "relative_main_file": save_result["relative_main_file"],
                "relative_executive_brief": save_result.get("relative_executive_brief", ""),
                "is_factored": save_result["is_factored"],
                "parts_metadata": save_result["parts_metadata"]
            }
            index_result = update_or_split_index(
                index_path,
                entry_data,
                max_lines=args.max_lines,
                lang=args.lang
            )
        
        output = {
            "status": "success",
            "base_name": base_name,
            "title": doc_title,
            "lang": args.lang,
            "is_text_input": is_text_input,
            "summary": summary,
            "index_action": index_result,
            **save_result
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        
    except Exception as e:
        error_output = {
            "status": "error",
            "message": str(e)
        }
        print(json.dumps(error_output, ensure_ascii=False, indent=2))
        sys.exit(1)

if __name__ == "__main__":
    main()

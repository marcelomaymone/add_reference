import os
import sys
import json
import unittest
import tempfile
import shutil
from pathlib import Path

# Adiciona o diretório do script ao sys.path
sys.path.insert(0, str(Path(__file__).parent))

import convert_to_md

class TestConvertToMd(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_clean_markdown_content_removes_page_markers(self):
        sample_text = (
            "<!-- Página 1 -->\n"
            "Reference number ISO/IEC/IEEE 29148:2011(E)\n"
            "Page 1 of 90\n"
            "\x0c"
            "<!-- Page 2 -->\n"
            "Systems and software engineering\n"
            "Página 2 de 90\n"
            "1. Overview\n"
        )
        cleaned = convert_to_md.clean_markdown_content(sample_text)
        self.assertNotIn("<!-- Página", cleaned)
        self.assertNotIn("<!-- Page", cleaned)
        self.assertNotIn("Page 1 of 90", cleaned)
        self.assertNotIn("Página 2 de 90", cleaned)
        self.assertNotIn("\x0c", cleaned)
        self.assertIn("1. Overview", cleaned)
        self.assertIn("Reference number ISO/IEC/IEEE 29148:2011(E)", cleaned)

    def test_extract_chunk_topics(self):
        chunk = (
            "# Clause 5: Process Definition\n"
            "Some introductory text here.\n"
            "## 5.2 Stakeholder Requirements Definition Process\n"
            "Details about stakeholder requirements.\n"
            "### 5.2.1 Stakeholder Identification\n"
            "Identifying people involved.\n"
        )
        topics = convert_to_md.extract_chunk_topics(chunk, lang="eng-US")
        self.assertIsInstance(topics, str)
        self.assertTrue(len(topics) > 0)
        self.assertIn("5.2", topics)
        self.assertIn("Stakeholder", topics)

    def test_split_and_save_markdown_factoring_and_navigation(self):
        # Gera mais de 450 linhas
        lines = [f"Line {i}: Content description regarding section {i // 50}" for i in range(1, 1001)]
        lines[10] = "## Section 1: Core Concepts"
        lines[500] = "## Section 2: Technical Specifications"
        content = "\n".join(lines)

        result = convert_to_md.split_and_save_markdown(
            content=content,
            target_dir=self.test_dir,
            base_name="standard_doc",
            max_lines=450,
            lang="eng-US"
        )

        self.assertTrue(result["is_factored"])
        self.assertGreaterEqual(result["parts_count"], 2)
        self.assertIn("parts_metadata", result)
        self.assertEqual(len(result["parts_metadata"]), result["parts_count"])

        # Verifica Parte 01
        part1_path = Path(result["files"][0])
        part1_content = part1_path.read_text(encoding="utf-8")
        self.assertIn("Factored Document Index", part1_content)
        self.assertIn("[Part 01]", part1_content)
        self.assertIn("[Part 02]", part1_content)

        # Verifica Parte 02
        part2_path = Path(result["files"][1])
        part2_content = part2_path.read_text(encoding="utf-8")
        self.assertIn("> **Navigation:** [← Return to Factored Document Index (Part 01)]", part2_content)
        self.assertIn("Part 2 of", part2_content)

    def test_update_or_split_index_normal_and_overflow(self):
        index_file = Path(self.test_dir) / "index.md"

        sample_entry = {
            "title": "IEEE 29148 Standard",
            "summary": "Systems and software engineering requirements standard.",
            "relative_main_file": "./ieee_29148_01.md",
            "is_factored": True,
            "parts_metadata": [
                {"part_number": 1, "relative_path": "./ieee_29148_01.md", "topics_summary": "Clause 1 to 4"},
                {"part_number": 2, "relative_path": "./ieee_29148_02.md", "topics_summary": "Clause 5 to 7"}
            ]
        }

        # Atualização normal
        convert_to_md.update_or_split_index(index_file, sample_entry, max_lines=450, lang="eng-US")
        self.assertTrue(index_file.exists())
        index_content = index_file.read_text(encoding="utf-8")
        self.assertIn("IEEE 29148 Standard", index_content)
        self.assertIn("Clause 1 to 4", index_content)

        # Teste de transbordo (overflow) > 450 linhas
        # Preenche com entradas simuladas até passar de 450 linhas
        dummy_entries = []
        for i in range(1, 20):
            entry = {
                "title": f"Document Specification {i}",
                "summary": f"Detailed specification document number {i}.",
                "relative_main_file": f"./doc_{i:02d}_01.md",
                "is_factored": True,
                "parts_metadata": [
                    {"part_number": p, "relative_path": f"./doc_{i:02d}_{p:02d}.md", "topics_summary": f"Section {p} details"}
                    for p in range(1, 10)
                ]
            }
            dummy_entries.append(entry)

        for entry in dummy_entries:
            convert_to_md.update_or_split_index(index_file, entry, max_lines=50, lang="eng-US") # limite menor para testar fatoração

        master_index_content = index_file.read_text(encoding="utf-8")
        self.assertIn("Master Reference Index", master_index_content)
        self.assertIn("index_01.md", master_index_content)

        index_01_file = Path(self.test_dir) / "index_01.md"
        self.assertTrue(index_01_file.exists())


    def test_single_file_not_factored(self):
        content = "# Short Document\n\nThis is a brief specification within 50 lines."
        result = convert_to_md.split_and_save_markdown(
            content=content,
            target_dir=self.test_dir,
            base_name="short_spec",
            max_lines=450,
            lang="eng-US"
        )
        self.assertFalse(result["is_factored"])
        self.assertEqual(result["parts_count"], 1)
        self.assertEqual(len(result["files"]), 1)
        self.assertEqual(result["relative_main_file"], "./short_spec.md")
        saved_file = Path(result["files"][0])
        self.assertTrue(saved_file.exists())
        self.assertIn("# Short Document", saved_file.read_text(encoding="utf-8"))

    def test_cli_execution_with_update_index(self):
        import subprocess
        sample_doc = Path(self.test_dir) / "sample_input.txt"
        sample_doc.write_text("# Chapter 1: Introduction\nBasic system definitions.\n\n<!-- Página 1 -->\nPage 1 of 5\nMore details.", encoding="utf-8")
        
        script_path = Path(__file__).parent / "convert_to_md.py"
        cmd = [
            sys.executable,
            str(script_path),
            str(sample_doc),
            self.test_dir,
            "--name", "sample_input",
            "--title", "Sample Standard Specification",
            "--update-index",
            "--lang", "eng-US"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        out_json = json.loads(res.stdout)
        self.assertEqual(out_json["status"], "success")
        self.assertIn("index_action", out_json)
        
        index_file = Path(self.test_dir) / "index.md"
        self.assertTrue(index_file.exists())
        index_text = index_file.read_text(encoding="utf-8")
        self.assertIn("Sample Standard Specification", index_text)
        self.assertNotIn("<!-- Página", index_text)
        self.assertNotIn("Page 1 of 5", index_text)

    def test_yaml_frontmatter_and_boundary_aware_chunking(self):
        # Cria seções com tabelas que não devem ser cortadas ao meio
        sections = []
        for s in range(1, 15):
            sec_lines = [
                f"## Section {s}: Process Architecture and Data Flow {s}",
                f"Description paragraph explaining normative clause {s}.1 in full detail.",
                "",
                "| Step ID | Operation | Responsibility |",
                "| --- | --- | --- |",
                f"| OP-{s}-1 | Analysis | System Architect |",
                f"| OP-{s}-2 | Verification | QA Lead |",
                f"| OP-{s}-3 | Approval | Project Manager |",
                ""
            ]
            sec_lines.extend([f"Text explanation note {i} for section {s}." for i in range(1, 40)])
            sections.append("\n".join(sec_lines))

        full_content = "\n\n".join(sections)

        result = convert_to_md.split_and_save_markdown(
            content=full_content,
            target_dir=self.test_dir,
            base_name="process_standard",
            max_lines=250, # limite para forçar múltiplas partes
            lang="eng-US"
        )

        self.assertTrue(result["is_factored"])
        self.assertIn("executive_brief_file", result)
        
        # 1. Verifica Frontmatter YAML em todas as partes
        for file_path in result["files"]:
            text = Path(file_path).read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---"), f"Arquivo {file_path} não inicia com YAML frontmatter")
            # Extrai o frontmatter
            parts = text.split("---", 2)
            self.assertGreaterEqual(len(parts), 3)
            yaml_header = parts[1]
            self.assertIn("document:", yaml_header)
            self.assertIn("part:", yaml_header)
            self.assertIn("total_parts:", yaml_header)
            self.assertIn("key_topics:", yaml_header)

            # 2. Verifica integridade de tabelas (nenhuma tabela cortada)
            lines = text.splitlines()
            pipe_lines = [l for l in lines if l.strip().startswith("|")]
            if pipe_lines:
                # Se tem tabela, deve ter o cabeçalho | --- |
                header_sep = [l for l in pipe_lines if "---" in l]
                self.assertTrue(len(header_sep) > 0, "Tabela sem separador de cabeçalho detectada no recorte")

    def test_generate_executive_brief_structure_and_limits(self):
        sample_doc = (
            "# ISO/IEC/IEEE 99999 Standard\n\n"
            "1 Scope\n"
            "This International Standard specifies the mandatory engineering requirements for critical systems.\n\n"
            "2 Normative References\n"
            "ISO 9001 Quality Management.\n\n"
            "3 Terms and Definitions\n"
            "SyRS: System Requirements Specification.\n"
            "OpsCon: Operational Concept Document.\n\n"
            "4 Process Requirements\n"
            "4.1 System Requirement Identification\n"
            "The project team shall identify all stakeholder needs.\n"
            "The requirements engineer shall verify uniqueness and traceability of each requirement.\n\n"
            "4.2 Interface Definition\n"
            "All physical and logical interfaces shall be formally documented in an ICD.\n"
        )

        brief_content = convert_to_md.generate_executive_brief(
            content=sample_doc,
            base_name="critical_standard",
            title="ISO/IEC/IEEE 99999 Standard",
            parts_metadata=[
                {"part_number": 1, "relative_path": "./critical_standard_01.md", "topics_summary": "1 Scope, 3 Terms"},
                {"part_number": 2, "relative_path": "./critical_standard_02.md", "topics_summary": "4 Process Requirements"}
            ],
            lang="eng-US"
        )

        self.assertIsInstance(brief_content, str)
        brief_lines = len(brief_content.splitlines())
        self.assertLessEqual(brief_lines, 300, f"Executive brief excedeu 300 linhas: {brief_lines}")
        self.assertIn("Executive Brief & Normative Core", brief_content)
        self.assertIn("Mandatory Rules", brief_content)
        self.assertIn("shall", brief_content.lower())
        self.assertIn("Lexicon", brief_content)
        self.assertIn("SyRS", brief_content)
        self.assertIn("Agent Fast Retrieval Protocol", brief_content)

    def test_search_reference_catalog_cli_query(self):
        # Cria arquivos de teste no diretório
        doc1 = Path(self.test_dir) / "test_doc_01.md"
        doc1.write_text(
            "---\ndocument: test_doc\npart: 1\n---\n# Architecture\nClause 5.1 Architecture definition is critical.",
            encoding="utf-8"
        )
        doc2 = Path(self.test_dir) / "test_doc_02.md"
        doc2.write_text(
            "---\ndocument: test_doc\npart: 2\n---\n# Verification Process\nClause 6.4 Verification shall be executed with automated test suites.",
            encoding="utf-8"
        )

        # Testa busca via função
        search_res = convert_to_md.search_reference_catalog(
            catalog_dir=self.test_dir,
            query_term="Verification shall be executed"
        )
        self.assertGreaterEqual(len(search_res), 1)
        first_match = search_res[0]
        self.assertIn("test_doc_02.md", first_match["file"])
        self.assertIn("Clause 6.4", first_match["snippet"])

        # Testa busca via CLI com --query
        import subprocess
        script_path = Path(__file__).parent / "convert_to_md.py"
        cmd = [
            sys.executable,
            str(script_path),
            "--query", "Verification shall be executed",
            self.test_dir
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        self.assertIn("test_doc_02.md", res.stdout)
        self.assertIn("Clause 6.4", res.stdout)

if __name__ == "__main__":
    unittest.main()



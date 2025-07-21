import pandas as pd
import re
import os

def sanitize_text(text):
    if isinstance(text, str):
        return text.replace("\n", " ").replace("\r", " ").strip()
    return text

# IEEE CSV
def parse_ieee_csv(file_path):
    df = pd.read_csv(file_path)
    records = []

    for _, row in df.iterrows():
        record = {
            "Database": "IEEE",
            "Authors": sanitize_text(row.get("Authors", "")),
            "Title": sanitize_text(row.get("Document Title", "")),
            "Journal": sanitize_text(row.get("Publication Title", "")),
            "Year": row.get("Publication Year", ""),
            "Volume": row.get("Volume", ""),
            "Issue": row.get("Issue", ""),
            "Pages": f"{row.get('Start Page', '')}-{row.get('End Page', '')}" if pd.notna(row.get("Start Page", "")) and pd.notna(row.get("End Page", "")) else "",
            "DOI": sanitize_text(row.get("DOI", "")),
            "URL": sanitize_text(row.get("PDF Link", "")),
            "Abstract": sanitize_text(row.get("Abstract", "")),
            "Keywords": sanitize_text(row.get("Author Keywords", ""))
        }
        records.append(record)
    return records

# Scopus RIS
def parse_ris_scopus(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    entries = []
    entry = {}
    current_key = ""
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("TY  -"):
            entry = {"Database": "Scopus"}
        elif line.startswith("ER  -"):
            entries.append(entry)
            entry = {}
        else:
            match = re.match(r'^([A-Z0-9]{2})\s*-\s*(.*)', line)
            if match:
                current_key, value = match.groups()
                if current_key in entry:
                    entry[current_key] += "; " + value
                else:
                    entry[current_key] = value
            else:
                if current_key in entry:
                    entry[current_key] += " " + line

    records = []
    for e in entries:
        record = {
            "Database": "Scopus",
            "Authors": sanitize_text(e.get("AU", "")),
            "Title": sanitize_text(e.get("TI", "")),
            "Journal": sanitize_text(e.get("JO", "")),
            "Year": e.get("PY", ""),
            "Volume": e.get("VL", ""),
            "Issue": e.get("IS", ""),
            "Pages": f"{e.get('SP', '')}-{e.get('EP', '')}" if "SP" in e and "EP" in e else "",
            "DOI": sanitize_text(e.get("DO", "")),
            "URL": sanitize_text(e.get("UR", "")),
            "Abstract": sanitize_text(e.get("AB", "")),
            "Keywords": sanitize_text(e.get("KW", ""))
        }
        records.append(record)
    return records

# ACM BibTeX
def parse_bib_acm(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = re.findall(r'@[\w]+\s*{[^@]*}', content, re.DOTALL)
    records = []

    for entry in entries:
        fields = dict(re.findall(r'(\w+)\s*=\s*[{"]([^}"]+)[}"]', entry, re.IGNORECASE))
        record = {
            "Database": "ACM",
            "Authors": sanitize_text(fields.get("author", "")),
            "Title": sanitize_text(fields.get("title", "")),
            "Journal": sanitize_text(fields.get("journal", "")),
            "Year": fields.get("year", ""),
            "Volume": fields.get("volume", ""),
            "Issue": fields.get("number", ""),
            "Pages": sanitize_text(fields.get("pages", "")),
            "DOI": sanitize_text(fields.get("doi", "")),
            "URL": sanitize_text(fields.get("url", "")),
            "Abstract": sanitize_text(fields.get("abstract", "")),
            "Keywords": sanitize_text(fields.get("keywords", ""))
        }
        records.append(record)
    return records

# IEEE BibTeX
def parse_bib_ieee(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = re.findall(r'@[\w]+\s*{[^@]*}', content, re.DOTALL)
    records = []

    for entry in entries:
        fields = dict(re.findall(r'(\w+)\s*=\s*[{"]([^}"]+)[}"]', entry, re.IGNORECASE))
        record = {
            "Database": "IEEE",
            "Authors": sanitize_text(fields.get("author", "")),
            "Title": sanitize_text(fields.get("title", "")),
            "Journal": sanitize_text(fields.get("journal", "")),
            "Year": fields.get("year", ""),
            "Volume": fields.get("volume", ""),
            "Issue": fields.get("number", ""),
            "Pages": sanitize_text(fields.get("pages", "")),
            "DOI": sanitize_text(fields.get("doi", "")),
            "URL": sanitize_text(fields.get("url", "")),
            "Abstract": sanitize_text(fields.get("abstract", "")),
            "Keywords": sanitize_text(fields.get("keywords", ""))
        }
        records.append(record)
    return records

# ScienceDirect TXT
def parse_sciencedirect(txt):
    entries = txt.strip().split("\n\n")
    records = []

    for entry in entries:
        lines = entry.split("\n")
        record = {
            "Database": "ScienceDirect",
            "Authors": "",
            "Title": "",
            "Journal": "",
            "Year": "",
            "Volume": "",
            "Issue": "",
            "Pages": "",
            "DOI": "",
            "URL": "",
            "Abstract": "",
            "Keywords": ""
        }

        try:
            record["Authors"] = sanitize_text(lines[0])
            record["Title"] = sanitize_text(lines[1])
            record["Journal"] = sanitize_text(lines[2])

            for i in range(3, len(lines)):
                line = lines[i]
                if "Volume" in line:
                    record["Volume"] = sanitize_text(line.replace("Volume", ""))
                elif re.match(r"\d{4}", line):
                    record["Year"] = sanitize_text(line)
                elif "Pages" in line:
                    record["Pages"] = sanitize_text(line.replace("Pages", ""))
                elif "Issue" in line:
                    record["Issue"] = sanitize_text(line.replace("Issue", ""))
                elif line.startswith("https://doi"):
                    record["DOI"] = sanitize_text(line)
                elif line.startswith("(") and "sciencedirect.com" in line:
                    record["URL"] = sanitize_text(line.strip("()"))
                elif line.lower().startswith("abstract"):
                    record["Abstract"] = sanitize_text(line.split(":", 1)[-1])
                elif line.lower().startswith("keywords"):
                    record["Keywords"] = sanitize_text(line.split(":", 1)[-1])

        except Exception as e:
            print(f"Erro ao processar entrada: {e}")
        records.append(record)
    return records

# Caminho para a pasta "referencias"
referencias_dir = os.path.join(os.path.dirname(__file__), "referencias")
todos_registros = []

# Processa os arquivos
for filename in os.listdir(referencias_dir):
    path = os.path.join(referencias_dir, filename)

    try:
        if filename.endswith(".csv"):
            registros = parse_ieee_csv(path)
        elif filename.endswith(".ris"):
            registros = parse_ris_scopus(path)
        elif filename.endswith(".bib") and "acm" in filename.lower():
            registros = parse_bib_acm(path)
        elif filename.endswith(".bib") and "ieee" in filename.lower():
            registros = parse_bib_ieee(path)
        elif filename.endswith(".txt"):
            with open(path, "r", encoding="utf-8") as f:
                conteudo = f.read()
            registros = parse_sciencedirect(conteudo)
        else:
            print(f"Tipo de arquivo não suportado: {filename}")
            continue

        todos_registros.extend(registros)
        print(f"[✓] Processado: {filename}")
    except Exception as e:
        print(f"[X] Erro ao processar {filename}: {e}")

# Cria DataFrame e salva como CSV (ponto e vírgula para Excel europeu)
df_merged = pd.DataFrame(todos_registros)
output_csv = os.path.join(os.path.dirname(__file__), "referencias_unificadas.csv")
df_merged.to_csv(output_csv, index=False, encoding='utf-8-sig', sep=';')

print(f"\n📄 Arquivo final gerado com sucesso: {output_csv}")

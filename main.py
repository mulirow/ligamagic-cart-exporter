import sys
import re
from typing import Dict, Optional, Union
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
HTML_INPUT_FILE = "carrinho_in.html"
OUTPUT_EXCEL_FILE = "carrinho_out.xlsx"

# CSS Selectors
SELECTORS = {
    "item_container": "div.table-cart-row",
    "link": "h3.checkout-product--title a",
    "nome_pt": "h3.checkout-product--title",
    "nome_en": "p.checkout-product--subtitle",
    "descriptions": "p.checkout-product--description",
    "quantidade": "input.checkout-product--qty",
    "preco": "p.checkout-product--price.new",
}

# Search Keywords (Must remain in Portuguese to match HTML content)
KEYWORDS = {
    "idioma": [
        "Alemão",
        "Chinês",
        "Espanhol",
        "Francês",
        "Inglês",
        "Italiano",
        "Japonês",
        "Coreano",
        "Português",
        "Russo",
        "Phyrexiano",
    ],
    "condicao": ["Aberto", "Lacrado", "Novo", "Usado", "Nova", "Usada", "Danificada"],
    "extras": ["Foil", "Promo", "Pre Release"],
}


def clean_text(text: Optional[str]) -> str:
    """Removes extra whitespace from strings."""
    if text is None:
        return ""
    return " ".join(text.split())


def parse_price(price_str: str) -> float:
    """
    Converts a price string (ex: 'R$ 1.250,50') into a float (1250.50).
    """
    if not price_str:
        return 0.0

    cleaned = price_str.replace("R$", "").replace("€", "").replace("$", "").strip()

    cleaned = cleaned.replace(".", "")

    cleaned = cleaned.replace(",", ".")

    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def extract_content_in_parentheses(text: str) -> str:
    """
    Extracts content between parenthesis in a given string.
    Ex: 'Near Mint (NM)' -> 'NM'
    """
    match = re.search(r"\((.*?)\)", text)
    if match:
        return match.group(1)
    return text


def extract_item_data(
    item_soup: BeautifulSoup, selectors: Dict[str, str]
) -> Optional[Dict[str, Union[str, int, float]]]:
    """
    Extracts data from a single HTML item container.
    Returns a dictionary with the data or None if extraction fails.
    """
    try:
        # Basic extraction
        link_tag = item_soup.select_one(selectors["link"])
        name_pt_tag = item_soup.select_one(selectors["nome_pt"])
        name_en_tag = item_soup.select_one(selectors["nome_en"])
        price_tag = item_soup.select_one(selectors["preco"])
        qty_tag = item_soup.select_one(selectors["quantidade"])

        # Safety check for essential elements
        if not all([link_tag, name_pt_tag, qty_tag]):
            return None

        link = link_tag["href"]
        nome_pt = clean_text(name_pt_tag.text)
        nome_en = clean_text(name_en_tag.text) if name_en_tag else ""
        price_text = clean_text(price_tag.text) if price_tag else "0"
        preco = parse_price(price_text)
        quantidade = int(qty_tag["value"])

        # Initialize classification variables
        expansao = "N/A"
        idioma = "N/A"
        condicao = "N/A"
        extras_list = []

        # Logic to classify descriptions
        description_tags = item_soup.select(selectors["descriptions"])
        remaining_descriptions = []

        for desc in description_tags:
            text = clean_text(desc.text)
            matched = False

            # Check against keywords
            if any(kw in text for kw in KEYWORDS["idioma"]):
                idioma = text
                matched = True
            elif any(kw in text for kw in KEYWORDS["condicao"]):
                condicao = extract_content_in_parentheses(text)
                matched = True
            elif any(kw in text for kw in KEYWORDS["extras"]):
                extras_list.append(text)
                matched = True

            if not matched:
                remaining_descriptions.append(text)

        # Join extras if multiple found (e.g., "Foil, Promo")
        extras = ", ".join(extras_list) if extras_list else "N/A"

        # Heuristic: The expansion is usually the remaining unmatched description
        if remaining_descriptions:
            expansao = remaining_descriptions[0]

        # Return dict with keys for the Excel header
        return {
            "Nome (Português)": nome_pt,
            "Nome (Inglês)": nome_en,
            "Expansão": expansao,
            "Idioma": idioma,
            "Condição": condicao,
            "Extras": extras,
            "Link": link,
            "Quantidade": quantidade,
            "Preço Unitário": preco,
        }

    except Exception as e:
        print(f"   - Warning: Failed to parse specific item. Details: {e}")
        return None


def process_html_to_excel(input_file: str, output_file: str, selectors: Dict[str, str]):
    """Main function to read HTML, parse data, and save to Excel."""

    print(f"1. Reading local HTML file: '{input_file}'...")
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"\nERROR: File '{input_file}' not found.")
        sys.exit(1)

    soup = BeautifulSoup(html_content, "html.parser")
    items_html = soup.select(selectors["item_container"])

    if not items_html:
        print(
            f"\nERROR: No cart items found using selector '{selectors['item_container']}'."
        )
        return

    print(f"2. Found {len(items_html)} items. Extracting information...")

    extracted_items = []
    for item_soup in items_html:
        data = extract_item_data(item_soup, selectors)
        if data:
            extracted_items.append(data)

    if not extracted_items:
        print("\nERROR: No data could be extracted. Please check selectors.")
        return

    print("3. Creating Excel spreadsheet...")
    try:
        df = pd.DataFrame(extracted_items)
        df["Preço Unitário"] = df["Preço Unitário"].round(2)

        df.to_excel(output_file, index=False)
        print(f"\nDone! Data successfully saved to '{output_file}'")
    except Exception as e:
        print(f"\nERROR: Failed to save Excel file. Details: {e}")


if __name__ == "__main__":
    process_html_to_excel(HTML_INPUT_FILE, OUTPUT_EXCEL_FILE, SELECTORS)

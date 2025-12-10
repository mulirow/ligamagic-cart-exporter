import sys
import re
from typing import Dict, Optional, Union
from dataclasses import dataclass
from pathlib import Path
import pandas as pd
from bs4 import BeautifulSoup

# --- CONFIGURATION ---
INPUT_FILE = Path("carrinho_in.html")
OUTPUT_FILE = Path("carrinho_out.xlsx")

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


@dataclass
class CardItem:
    """Represents an extracted cart item."""

    nome_pt: str
    nome_en: str
    expansao: str
    idioma: str
    condicao: str
    extras: str
    link: str
    quantidade: int
    preco_unitario: float

    @property
    def preco_total(self) -> float:
        """Calculates total price automatically."""
        return self.quantidade * self.preco_unitario

    def to_dict(self) -> Dict[str, Union[str, int, float]]:
        """Converts to dictionary with keys for the Excel header."""
        return {
            "Nome (Português)": self.nome_pt,
            "Nome (Inglês)": self.nome_en,
            "Expansão": self.expansao,
            "Idioma": self.idioma,
            "Condição": self.condicao,
            "Extras": self.extras,
            "Quantidade": self.quantidade,
            "Preço Unitário": self.preco_unitario,
            "Preço Total": self.preco_total,
            "Link": self.link,
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

    clean_nums = re.sub(r"[^\d,]", "", price_str)

    clean_nums = clean_nums.replace(",", ".")

    try:
        return float(clean_nums)
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
) -> Optional[CardItem]:
    """
    Extracts data from a single HTML item container.
    Returns a CardItem object or None if extraction fails.
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

        # Return Data Class
        return CardItem(
            nome_pt=nome_pt,
            nome_en=nome_en,
            expansao=expansao,
            idioma=idioma,
            condicao=condicao,
            extras=extras,
            link=link,
            quantidade=quantidade,
            preco_unitario=preco,
        )

    except Exception as e:
        print(f"   - Warning: Failed to parse specific item. Details: {e}")
        return None


def process_html_to_excel(
    input_file: Path, output_file: Path, selectors: Dict[str, str]
):
    """Main function to read HTML, parse data, and save to Excel."""

    print(f"1. Reading local HTML file: '{input_file}'...")
    if not input_file.exists():
        print(f"\nERROR: File '{input_file}' not found.")
        sys.exit(1)

    html_content = input_file.read_text(encoding="utf-8")

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
        item_obj = extract_item_data(item_soup, selectors)
        if item_obj:
            extracted_items.append(item_obj.to_dict())

    if not extracted_items:
        print("\nERROR: No data could be extracted. Please check selectors.")
        return

    print("3. Creating Excel spreadsheet...")
    try:
        df = pd.DataFrame(extracted_items)
        if "Preço Unitário" in df.columns:
            df["Preço Unitário"] = df["Preço Unitário"].round(2)
        if "Preço Total" in df.columns:
            df["Preço Total"] = df["Preço Total"].round(2)

        df.to_excel(output_file, index=False)
        print(f"\nDone! Data successfully saved to '{output_file.absolute()}'")
    except Exception as e:
        print(f"\nERROR: Failed to save Excel file. Details: {e}")


if __name__ == "__main__":
    process_html_to_excel(INPUT_FILE, OUTPUT_FILE, SELECTORS)

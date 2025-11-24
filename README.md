# Exportador de Carrinho LigaMagic

Uma ferramenta em Python projetada para extrair dados de carrinhos de compras de lojas baseadas na plataforma LigaMagic e exportar a lista para uma planilha Excel organizada.

Esta ferramenta é útil para jogadores e lojistas que precisam fazer backup do carrinho, organizar grandes pedidos, conferir itens ou migrar buylists para outras plataformas.

## Funcionalidades

- **Leitura Local:** Funciona lendo um arquivo HTML salvo (contornando a necessidade de login/sessão via script).
- **Classificação Inteligente:** Detecta e separa automaticamente:
  - Nome da Carta
  - Edição/Expansão
  - Idioma (ex: Português, Inglês, Japonês, Phyrexiano)
  - Condição (ex: NM, SP, D)
  - Extras (Foil, Promo, Pre-release)
- **Saída em Excel:** Gera um arquivo `.xlsx` formatado com colunas separadas para fácil filtragem.

## Pré-requisitos

- Python 3.x instalado.
- Bibliotecas: `pandas`, `beautifulsoup4`, `openpyxl`.

Você pode instalar as dependências com o comando:

```bash
pip install pandas beautifulsoup4 openpyxl
```

ou, dentro da pasta do projeto:

```bash
pip install -r requirements.txt
```

## Como Usar

Como o carrinho de compras é protegido por sessão de usuário, o script não acessa o site diretamente. Você precisa salvar a página manualmente:

1. **Salvar a Página do Carrinho:**
   - Acesse o carrinho/checkout da loja no seu navegador.
   - Clique com o botão direito na página e selecione **"Salvar como..."**.
   - Salve o arquivo com o nome `carrinho_in.html` na mesma pasta onde está o script.

2. **Executar o Script:**
   Abra o terminal na pasta do projeto e execute:
   ```bash
   python main.py
   ```

3. **Verificar o Resultado:**
   - O script irá gerar um arquivo chamado `carrinho_out.xlsx` contendo seus dados organizados.
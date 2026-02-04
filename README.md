# Nkrane-GT: Enhanced Machine Translation with Terminology Control

[![Python 3.7+](https://img.shields.io/badge/python-3.7+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Nkrane-GT ("Nkrane - Google Translate") is a Python library that enhances Google Translate with **terminology control** for low-resource languages, with a focus on Ghanaian and African languages.

It solves the problem of inconsistent translations for critical terms by allowing you to enforce specific translations for nouns and noun phrases while letting Google Translate handle the grammatical structure.

---

## 🌍 Why Nkrane-GT?

Standard machine translation often struggles with:
- **Inconsistent terminology** - The same word translated differently in different contexts
- **Named entities** - People names, place names, cultural terms mistranslated
- **Domain-specific vocabulary** - Technical, medical, or legal terms poorly handled
- **Low-resource languages** - Limited training data for African languages

**Nkrane-GT solves this by:**
1. Extracting noun phrases from source text using NLP (spaCy)
2. Matching them against your terminology dictionary
3. Replacing content words with placeholders
4. Translating with Google Translate (grammar + stopwords)
5. Restoring your terminology with proper case preservation

---

## 🚀 Features

| Feature | Description |
|---------|-------------|
| **Terminology Control** | Enforce specific translations for key terms |
| **Built-in Dictionaries** | Pre-loaded with 860K+ terms for Akan (Twi), Ewe, and Ga |
| **Stopword Handling** | Intelligently leaves stopwords ("a", "the", "of") for natural translation |
| **Case Preservation** | Matches capitalization of original text |
| **Custom Dictionaries** | Load your own CSV terminology files |
| **Batch Translation** | Translate multiple texts efficiently |
| **CLI Interface** | Command-line tool for quick translations |
| **Noun Phrase Extraction** | Uses spaCy for intelligent phrase detection |

---

## 📦 Installation

### From Source

```bash
git clone https://github.com/yourusername/nkrane-gt.git
cd nkrane-gt
pip install -e .
```

### Requirements

```bash
pip install pandas spacy requests
python -m spacy download en_core_web_sm
```

---

## 🎯 Quick Start

### Basic Translation

```python
from nkrane_gt import NkraneTranslator

# Initialize with built-in Akan (Twi) dictionary
translator = NkraneTranslator(target_lang='ak')

# Translate
result = translator.translate("I want to buy a house and a car.")
print(result['text'])
# Output: "ME pɛ sɛ wotɔ ofie ne kar."
```

### With Custom Terminology

```python
# Create custom CSV
cat > my_terms.csv << EOF
text,translation
house,ofie
car,ntentan
school,sukuu
EOF

# Use custom + built-in dictionary
translator = NkraneTranslator(
    target_lang='ak',
    terminology_source='my_terms.csv'
)

result = translator.translate("I want to buy a house.")
print(result['text'])
```

### Batch Translation

```python
texts = [
    "Buy a house today.",
    "The car is fast.",
    "Go to school."
]

results = translator.batch_translate(texts)
for r in results:
    print(f"{r['original']} -> {r['text']}")
```

---

## 🔧 Supported Languages

### Target Languages (Built-in Dictionaries)

| Code | Language | Terms Available |
|------|----------|----------------|
| `ak` | Akan (Twi) | 860,000+ |
| `ee` | Ewe | 860,000+ |
| `gaa` | Ga | 860,000+ |

### Source Languages

Any language supported by Google Translate (English, French, Spanish, etc.)

---

## 📚 How It Works

### The Translation Pipeline

```
Input: "I want to buy a house."
         ↓
1. Noun Phrase Extraction (spaCy)
   → Finds: "I" (pronoun), "a house" (noun chunk)
   → Filters stopwords: "a house" → "house"
   → Skips pronouns: "I" ignored
         ↓
2. Dictionary Matching
   → "house" in dictionary? ✓ → "ofie"
         ↓
3. Preprocessing
   → "I want to buy <1>."
         ↓
4. Google Translate
   → "ME pɛ sɛ wotɔ <1>."
         ↓
5. Postprocessing (case-matched)
   → "ME pɛ sɛ wotɔ ofie."
         ↓
Output: "ME pɛ sɛ wotɔ ofie."
```

### Key Innovations

**Stopword Preservation**
- Old: "a house" → `<1>` → translated stopword in wrong position
- New: "a house" → "a `<1>`" → stopword translated naturally by Google

**Case Matching**
- Input: "House" → Output: "Ofie"
- Input: "house" → Output: "ofie"
- Input: "HOUSE" → Output: "OFIE"

---

## 🛠️ Advanced Usage

### CLI Commands

```bash
# Translate text
nkrane-gt translate "Hello world" --target ak

# List available terminology
nkrane-gt list

# Export terminology to JSON
nkrane-gt export --terminology my_terms.csv --format json

# Create sample terminology file
nkrane-gt sample --output sample_terms.csv
```

### Custom Terminology Format

CSV with columns (auto-detected):
- `text` / `english` / `term` / `word` - Source term
- `translation` / `text_translated` / `target` - Target translation

Example:
```csv
text,translation
custom house,me ofie
big car,ntentan kɛse
```

### Without Built-in Dictionary

```python
# Use only your custom terms
translator = NkraneTranslator(
    target_lang='ak',
    terminology_source='my_terms.csv',
    use_builtin=False  # Skip built-in dictionary
)
```

---

## 🧪 Development

### Running Tests

```bash
pip install pytest
pytest tests/
```

### Project Structure

```
nkrane-gt/
├── nkrane_gt/
│   ├── __init__.py          # Package exports
│   ├── translator.py        # Main NkraneTranslator class
│   ├── terminology_manager.py  # Dictionary & NLP logic
│   ├── language_codes.py    # Language code mappings
│   ├── utils.py            # Helper functions
│   ├── cli.py              # Command-line interface
│   └── data/               # Built-in dictionaries
│       ├── nouns_ak.pkl    # Akan/Twi terms
│       ├── nouns_ee.pkl    # Ewe terms
│       └── nouns_gaa.pkl   # Ga terms
├── tests/
├── setup.py
└── README.md
```

---

## 📖 Citation

If you use Nkrane-GT in your research, please cite:

```bibtex
@software{nkrane_gt,
  title={Nkrane-GT: Enhanced Machine Translation with Terminology Control},
  author={Your Name},
  year={2024},
  url={https://github.com/yourusername/nkrane-gt}
}
```

---

## 🤝 Contributing

Contributions welcome! Areas of interest:
- Additional language support
- Improved noun phrase extraction
- Domain-specific terminology packs
- Performance optimizations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

## 🙏 Acknowledgments

- Built on [Google Translate](https://translate.google.com/) for base translation
- Uses [spaCy](https://spacy.io/) for NLP processing
- Inspired by the need for better African language translation tools

**"Nkrane"** means "translation" or "interpreter" in Akan/Twi.

---

## 📧 Contact

- Issues: [GitHub Issues](https://github.com/yourusername/nkrane-gt/issues)
- Email: your.email@example.com

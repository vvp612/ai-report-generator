"""Generate the stock branded .pptx template (rebrand by editing brand colors,
or point PPTX_TEMPLATE at a client deck).

Usage: python make_template.py
"""
from core.deck import DEFAULT_TEMPLATE, ensure_template

if __name__ == "__main__":
    print("template written:", ensure_template(DEFAULT_TEMPLATE))

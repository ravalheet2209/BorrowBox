import collections
from pptx import Presentation

prs = Presentation(r'e:\\internship 8sem\\newdesign\\Abstract_Pro_Design.pptx')

with open('layouts.txt', 'w', encoding='utf-8') as f:
    f.write("Slide Layouts:\n")
    for i, layout in enumerate(prs.slide_layouts):
        f.write(f"[{i}] {layout.name}\n")
        for j, shape in enumerate(layout.placeholders):
            f.write(f"  - Placeholder [{j}]: {shape.name} ({shape.placeholder_format.type})\n")

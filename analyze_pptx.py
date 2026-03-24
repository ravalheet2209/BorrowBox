import collections
from pptx import Presentation

prs = Presentation(r'e:\\internship 8sem\\newdesign\\Abstract_Pro_Design.pptx')

print("Slide Layouts:")
for i, layout in enumerate(prs.slide_layouts):
    print(f"[{i}] {layout.name}")
    for j, shape in enumerate(layout.placeholders):
        print(f"  - Placeholder [{j}]: {shape.name} ({shape.placeholder_format.type})")

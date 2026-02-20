from svglib.svglib import svg2rlg
from reportlab.graphics import renderPM

drawing = svg2rlg('assets/bkn_logo.svg')
renderPM.drawToFile(drawing, 'assets/bkn_logo.png', fmt="PNG")
print("Rendered successfully.")

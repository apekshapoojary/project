from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import os

def generate_certificate(user_name, event_name, date, output_path):
    # Set up the canvas
    c = canvas.Canvas(output_path, pagesize=landscape(letter))
    width, height = landscape(letter)

    # Use template if exists, else use standard design
    template_path = "static/images/cert_template.png"
    if os.path.exists(template_path):
        c.drawImage(template_path, 0, 0, width=width, height=height)
        
        # Participant Name (Centered right above the line at y=194)
        c.setFont("Times-BoldItalic", 34)
        c.setFillColor(HexColor('#0d2c54')) # Navy blue matching the borders
        c.drawCentredString(width/2, 208, user_name)
        
        # Event Info (Centered in the gap between the line and the footer text)
        c.setFont("Helvetica-Bold", 22)
        c.setFillColor(HexColor('#c59b27')) # Gold/mustard accent matching the graphics
        c.drawCentredString(width/2, 135, event_name)
        
        # Date (Centered at the very bottom below the footer text)
        c.setFont("Helvetica", 13)
        c.setFillColor(HexColor('#64748b')) # Muted slate grey
        c.drawCentredString(width/2, 45, f"Date: {date}")
        
    else:
        # Fallback Designer Look
        c.setFillColor(HexColor('#0f172a'))
        c.rect(0, 0, width, height, fill=1)
        
        c.setStrokeColor(HexColor('#8b5cf6'))
        c.setLineWidth(15)
        c.rect(20, 20, width-40, height-40)

        # Participant Name (Centered)
        c.setFont("Helvetica-Bold", 45)
        c.setFillColor(HexColor('#ffffff'))
        c.drawCentredString(width/2, height/2 + 0.2*inch, user_name)
        
        # Event Info
        c.setFont("Helvetica", 20)
        c.drawCentredString(width/2, height/2 - 0.8*inch, f"Participated in {event_name}")
        
        # Date
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height/2 - 2.5*inch, f"Validated on {date}")
        
        # Signature Placeholder
        c.setFont("Helvetica-Bold", 14)
        c.drawCentredString(width/2, 1.0*inch, "Official Digital Credential - EventLink AI")

    c.save()
    return output_path

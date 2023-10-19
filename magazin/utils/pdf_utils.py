from io import BytesIO
from reportlab.lib.pagesizes import letter, portrait, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from django.core.files.base import ContentFile
from magazin.models import Invoice
from datetime import datetime
import time
import random
import string

def generate_unique_invoice_number(order):
    # Generate a timestamp (current time in milliseconds)
    timestamp = int(time.time() * 1000)
    
    # Generate a random component (8 characters)
    random_component = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

    # Combine order ID, timestamp, and random component to create a unique invoice number
    invoice_number = f'INV-{order.id}-{timestamp}-{random_component}'
    
    return invoice_number

def generate_invoice_pdf(order, full_name):
    # Capture the current date and time
    current_datetime = datetime.now()

    # Create a BytesIO buffer to receive the PDF data
    buffer = BytesIO()

    # Create the PDF object
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    # Create a list to hold the elements of the PDF
    elements = []

    # Define the styles for the PDF
    styles = getSampleStyleSheet()
    normal_style = styles['Normal']
    bold_style = styles['Heading1']

    # Company information (left side)
    company_info = Paragraph("Label.M Unofficial E-commerce<br/>Bulevardul Libertatii<br/>Bucuresti, Romania<br/>Phone: 0732 123 456", normal_style)
    elements.append(company_info)

    # Add some space
    elements.append(Spacer(1, 12))

    # Custom order information
    shipping_address = order.shipping_address
    payment_method = order.payment_method

    # User information (right side)
    user_info = Paragraph(f"Customer:{full_name}<br/>Shipping Address:{shipping_address}<br/>Payment Method:{payment_method}", normal_style)
    elements.append(user_info)

    # Centered invoice order number
    invoice_number = generate_unique_invoice_number(order)
    invoice_number_text = Paragraph(f"Invoice Order #<br/>{invoice_number}", bold_style)
    elements.append(invoice_number_text)

    # Add some space
    elements.append(Spacer(1, 12))

    # Table to display product details
    data = [["Product Name", "Quantity", "Unit Price", "Subtotal"]]
    total_price = 0

    for product in order.products.all():
        price = product.price
        quantity = order.orderitem_set.get(product=product).quantity
        subtotal = price * quantity
        total_price += subtotal

        data.append([product.name, quantity, f'{price:.2f} Lei', f'{subtotal:.2f} Lei'])

    # Create the table
    table = Table(data, colWidths=[250, 80, 80, 90])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), (0.8, 0.8, 0.8)),
        ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), (0.96, 0.96, 0.96)),
        ('GRID', (0, 0), (-1, -1), 1, (0.6, 0.6, 0.6)),
    ]))

    elements.append(table)

    # Total price
    total_price_text = Paragraph(f'Total Price: {total_price:.2f} Lei', bold_style)
    elements.append(total_price_text)

    # Current date and time
    current_datetime_text = Paragraph(f'Invoice Date: {current_datetime.strftime("%Y-%m-%d %H:%M:%S")}', normal_style)
    elements.append(current_datetime_text)

    # Build the PDF document
    doc.build(elements)

    # Move the buffer's position to the beginning
    buffer.seek(0)

    # Return the PDF content and invoice number as a tuple
    return buffer, invoice_number

from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from ultralytics import YOLO
import os
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from django.views.decorators.cache import never_cache
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.http import HttpResponse

CUR_DIR = os.getcwd()
model = YOLO('savedModels\best.pt')

def generate_pdf(output_file, counts, annotated_image_path):
    doc = SimpleDocTemplate(output_file, pagesize=letter)

    # Create a list to hold the content of the PDF
    content = []

    # Get sample styles and define custom style for centered text
    styles = getSampleStyleSheet()
    centered_style = ParagraphStyle(name='Centered', alignment=1, parent=styles['Normal'])

    # Add a title to the PDF
    title = Paragraph("Analyse des figures Techniques ( Electriques )", styles['Title'])
    content.append(title)

    # Add some paragraphs with different formatting
    text = '''<i>Ce modèle a été conçu pour fournir des analyses détaillées concernant les données électriques et mécaniques. Grâce à ses capacités avancées de traitement du langage naturel,
    il peut extraire des informations précieuses à partir de chiffres, de graphiques et de données techniques dans le domaine de l'électromécanique. Que ce soit pour interpréter des résultats de tests,
    analyser des tendances ou expliquer des concepts complexes
    , ce modèle peut fournir des insights pertinents, simplifiant ainsi l'interprétation des données pour les experts du domaine.</i>'''
    formatted_text = Paragraph(text, styles['Normal'])
    content.append(formatted_text)

    # Add a spacer (blank line)
    spacer = Spacer(1, 20)  # Adjust the height as needed
    content.append(spacer)

    # Add a line (separator)
    line = HRFlowable(width="100%", thickness=1, lineCap='round', color='black')
    content.append(line)

    # Add a spacer (blank line)
    spacer = Spacer(1, 20)  # Adjust the height as needed
    content.append(spacer)

    # Add a colored and centered paragraph
    colored_text = "<font color='red'>Identification des composantes</font>"
    colored_paragraph = Paragraph(colored_text, centered_style)
    content.append(colored_paragraph)

    # Add a spacer (blank line)
    spacer = Spacer(1, 20)  # Adjust the height as needed
    content.append(spacer)

    img_path = annotated_image_path  # Use the path of the annotated image saved in the static directory
    img = Image(img_path)
    content.append(img)

        # Add a spacer (blank line)
    spacer = Spacer(1, 20)  # Adjust the height as needed
    content.append(spacer)


    # Add some paragraphs with different formatting
    text = '''Votre figure est composé des composantes suivantes : '''
    formatted_text = Paragraph(text, styles['Normal'])
    content.append(formatted_text)


        # Add a spacer (blank line)
    spacer = Spacer(1, 20)  # Adjust the height as needed
    content.append(spacer)


    # Define data for the table
    table_data = [
        ["Composante", "Count"]
    ]

    for key in counts.keys():
        table_data.append([model.names[key], counts[key]])

    # Create a table
    table = Table(table_data)

    # Apply style to the table
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    # Add the table to the content
    content.append(table)

    # Build the PDF document
    doc.build(content)

def generate_pdf_and_response(counts, annotated_image_path):
    output_pdf_path = os.path.join(CUR_DIR, 'static', 'formatted_pdf.pdf')
    generate_pdf(output_pdf_path, counts, annotated_image_path)
    
    with open(output_pdf_path, 'rb') as pdf_file:
        response = HttpResponse(pdf_file.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="formatted_pdf.pdf"'

    os.remove(output_pdf_path)
    return response

def predictor(request):
    if request.method == 'POST' and request.FILES['image_file']:
        image_file = request.FILES['image_file']

        fs = FileSystemStorage()
        image_path = os.path.join(CUR_DIR, 'temp_images', image_file.name)
        fs.save(image_path, image_file)

        results = model(image_path)

        counts = {}  # Replace this with your counts data

        annotated_image_path = os.path.join(CUR_DIR, 'static', 'annotated_images', 'annotated_image.jpg')
        im_array = results[0].plot(conf=False, font_size=1, labels=False, masks=False)
        im = PILImage.fromarray(im_array[..., ::-1])
        im.save(annotated_image_path)

        os.remove(image_path)

        return generate_pdf_and_response(counts, annotated_image_path)

    return render(request, 'main.html')

def download_pdf(request):
    counts = {}  # Replace this with your counts data
    annotated_image_path = os.path.join(CUR_DIR, 'static', 'annotated_images', 'annotated_image.jpg')
    return generate_pdf_and_response(counts, annotated_image_path)

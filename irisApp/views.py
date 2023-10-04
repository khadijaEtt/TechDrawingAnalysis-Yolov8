from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from ultralytics import YOLO
import os
from django.http import JsonResponse
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from django.views.decorators.cache import never_cache
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.http import HttpResponse
import random
CUR_DIR = os.getcwd()
model = YOLO('C:/Users/Lenovo/Desktop/projetStage/dossier_Prep/khadija_ETTOUIL_FSK_NLP_NonPFA_2023_3dsf/code/DjangoMLDeployment/DjangoMLDeployment/savedModels/best.pt')


def predictor(request):
    if request.method == 'POST' and request.FILES['image_file']:
        image_file = request.FILES['image_file']

        # Save the uploaded image temporarily
        fs = FileSystemStorage()
        image_path = os.path.join(CUR_DIR, 'temp_images', image_file.name)
        fs.save(image_path, image_file)

        # Perform object detection on the image
        results = model(image_path)

        # Process results and save the annotated image
        counts = {}
        for r in results:
            boxes = r.boxes.cpu().numpy()
            for box in boxes:
                cls = int(box.cls[0])
                if cls not in counts:
                    counts[cls] = 1
                else:
                    counts[cls] += 1

            im_array = r.plot(conf=False, font_size=2,line_width=1,labels=True)
            im = PILImage.fromarray(im_array[..., ::-1])

            # Save annotated image to a temporary location
            temp_image_path = os.path.join(CUR_DIR, 'temp_images', 'annotated_temp.jpg')
            im.save(temp_image_path)

            # Save the temporary image to the static directory
            # Save annotated image with the same name as the uploaded image
            annotated_image_name = f'annotated_{image_file.name}'
            annotated_image_path = os.path.join(CUR_DIR, 'static', 'annotated_images', annotated_image_name)       
            im.save(annotated_image_path)

            static_fs = FileSystemStorage(location=os.path.join(CUR_DIR, 'static'))
            static_fs.save(annotated_image_path, open(temp_image_path, 'rb'))

            # Clean up: Delete the temporary image
            os.remove(temp_image_path)

            # Create a function to generate the PDF
            def generate_pdf(output_file):
                # Set up the document
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


            # Generate the PDF
            generated_pdf_path = os.path.join(CUR_DIR, "static", "formatted_pdf.pdf")
            generate_pdf(generated_pdf_path)

            context = {
            'annotated_image_url': annotated_image_path.split('/')[-1],
            'generated_pdf_url': generated_pdf_path
        }

        action = request.POST.get('action')  # Get the value of the clicked button

        if action == 'predict':
            return render(request, 'main.html', context)
        elif action == 'download_pdf':
            with open(generated_pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="formatted_pdf.pdf"'
            os.remove(generated_pdf_path)  # Clean up: Delete the generated PDF file
            return response

    return render(request, 'main.html')

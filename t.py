from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from ultralytics import YOLO
import os
from PIL import Image as PILImage
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from django.http import HttpResponse

CUR_DIR = os.getcwd()
model = YOLO('savedModels\best.pt')

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

            im_array = r.plot(conf=False, font_size=1, labels=False, masks=False)
            im = PILImage.fromarray(im_array[..., ::-1])

            # Save annotated image to a temporary location
            temp_image_path = os.path.join(CUR_DIR, 'temp_images', f'annotated_temp_{image_file.name}')
            im.save(temp_image_path)

            # Save the temporary image to the static directory
            annotated_image_path = os.path.join('annotated_images', f'results_{image_file.name}')
            static_fs = FileSystemStorage(location=os.path.join(CUR_DIR, 'static'))
            static_fs.save(annotated_image_path, open(temp_image_path, 'rb'))

            # Clean up: Delete the temporary image
            os.remove(temp_image_path)

            # Generate the PDF
            def generate_pdf(output_file):
                doc = SimpleDocTemplate(output_file, pagesize=letter)
                content = []
                styles = getSampleStyleSheet()
                centered_style = ParagraphStyle(name='Centered', alignment=1, parent=styles['Normal'])
                title = Paragraph("Analyse des figures Techniques ( Electriques )", styles['Title'])
                content.append(title)
                spacer = Spacer(1, 20)
                content.append(spacer)
                line = HRFlowable(width="100%", thickness=1, lineCap='round', color='black')
                content.append(line)
                spacer = Spacer(1, 20)
                content.append(spacer)
                colored_text = "<font color='red'>Identification des composantes</font>"
                colored_paragraph = Paragraph(colored_text, centered_style)
                content.append(colored_paragraph)
                img_path = os.path.join(CUR_DIR, 'static', annotated_image_path)
                img = Image(img_path)
                content.append(img)
                text = '''Votre figure est composé des composantes suivantes : '''
                formatted_text = Paragraph(text, styles['Normal'])
                content.append(formatted_text)
                table_data = [["Composante", "Count"]]
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                for key in counts.keys():
                    table_data.append([model.names[key], counts[key]])
                content.append(table)
                doc.build(content)

            # Generate the PDF
            generated_pdf_path = os.path.join(CUR_DIR, "formatted_pdf.pdf")
            generate_pdf(generated_pdf_path)

            # Read the generated PDF and prepare a response to serve it for download
            with open(generated_pdf_path, 'rb') as pdf_file:
                response = HttpResponse(pdf_file.read(), content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="formatted_pdf.pdf"'

            # Clean up: Delete the generated PDF file
            os.remove(generated_pdf_path)

            # Display the result
            component_prediction = "Component: ..."  # Replace this with your component prediction logic
            return response

    return render(request, 'main.html')

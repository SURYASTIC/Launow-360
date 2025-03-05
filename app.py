from flask import Flask, render_template, request, redirect, url_for
import cv2
import numpy as np
import qrcode
from skimage import color
from fpdf import FPDF
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to calculate exact color fading percentage using Delta E
def calculate_color_fading(before_img, after_img):
    before_img = cv2.resize(before_img, (500, 500))
    after_img = cv2.resize(after_img, (500, 500))

    before_lab = color.rgb2lab(cv2.cvtColor(before_img, cv2.COLOR_BGR2RGB))
    after_lab = color.rgb2lab(cv2.cvtColor(after_img, cv2.COLOR_BGR2RGB))

    delta_e = np.sqrt(np.sum((before_lab - after_lab) ** 2, axis=2))
    color_fading_percentage = (np.mean(delta_e) / 100) * 100
    return round(color_fading_percentage, 2)

# Function to generate QR Code
def generate_qr_code(report):
    qr = qrcode.QRCode()
    qr.add_data(str(report))
    qr.make(fit=True)
    img_qr = qr.make_image(fill='black', back_color='white')
    qr_path = os.path.join(app.config['UPLOAD_FOLDER'], 'fabric_health_qr.png')
    img_qr.save(qr_path)
    return qr_path

# Function to generate PDF Report
def generate_pdf(report, qr_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Fabric Health Report", ln=True, align="C")
    pdf.ln(10)
    for key, value in report.items():
        pdf.cell(200, 10, txt=f"{key}: {value}", ln=True)
    pdf.ln(10)
    pdf.image(qr_path, x=80, y=None, w=50)
    pdf_path = os.path.join(app.config['UPLOAD_FOLDER'], 'Fabric_Health_Report.pdf')
    pdf.output(pdf_path)
    return pdf_path

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    before_img = request.files['before_img']
    after_img = request.files['after_img']

    if before_img and after_img:
        before_path = os.path.join(app.config['UPLOAD_FOLDER'], before_img.filename)
        after_path = os.path.join(app.config['UPLOAD_FOLDER'], after_img.filename)
        before_img.save(before_path)
        after_img.save(after_path)

        before_cv = cv2.imread(before_path)
        after_cv = cv2.imread(after_path)

        color_fading = calculate_color_fading(before_cv, after_cv)
        stain_removal = 100.0  # Default value
        fabric_health_score = round((stain_removal - color_fading) / 2) + 50

        report = {
            'Color Fading (%)': color_fading,
            'Stain Removal (%)': stain_removal,
            'Fabric Health Score': fabric_health_score
        }

        qr_path = generate_qr_code(report)
        pdf_path = generate_pdf(report, qr_path)

        return redirect(url_for('result', qr=qr_path, pdf=pdf_path))

    return redirect(url_for('index'))

@app.route('/result')
def result():
    qr = request.args.get('qr')
    pdf = request.args.get('pdf')
    return render_template('result.html', qr=qr, pdf=pdf)

if __name__ == '__main__':
     app.run(debug=True, host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
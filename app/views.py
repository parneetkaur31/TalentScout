from django.shortcuts import render
from django.http import HttpResponse
from django.http import JsonResponse
from django.core.files.storage import FileSystemStorage
from django.contrib import messages
import csv
from openai import OpenAI
import pandas as pd
import os
import PyPDF2 
from docx import Document  
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=api_key) if api_key else None



# Create your views here.
def index(request):
    return render(request, 'index.html')

def csv_to_string(filename):
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)
        data = list(reader)

    
    flat_list = [','.join(row) + '\n' for row in data]
    result_string = ''.join(flat_list)
    return result_string



def extract_fields(file, entered_prompt):
    extracted_str = csv_to_string(file)

    prompt = f"""
    Data:
    {extracted_str}

    Required:
    {entered_prompt}

    Return rows separated by ';' and columns by ','.
    Do not return code.
    """

    if not client:
        return "AI service is temporarily unavailable. Please try later."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful data extractor."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()




def generate_table(input_data):
    rows = input_data.strip(';').split(';')
    parsed_data = [row.split(',') for row in rows]
    num_columns = max(len(row) for row in parsed_data)
    column_names = [f"Column_{i+1}" for i in range(num_columns)]
    
    df = pd.DataFrame(parsed_data, columns=column_names)
    return df

def feature1(request):
    if request.method == 'POST' and request.FILES.get('file') and request.POST.get('textbox'):

        uploaded_file = request.FILES['file']
        entered_prompt = request.POST['textbox']
        
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(filename) 
        
        response = extract_fields(file_path, entered_prompt)
        table = generate_table(response)
        table_html = table.to_html(classes="table table-bordered", index=False)

        return render(request, 'feature1.html', {'table_html': table_html})
    
    return render(request, 'feature1.html')


def extract_cv_content(file_path):
    file_ext = os.path.splitext(file_path)[1].lower()

    if file_ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_ext == '.docx':
        return extract_text_from_docx(file_path)
    else:
        raise ValueError("Unsupported file format. Please upload a PDF or DOCX file.")

def extract_text_from_pdf(file_path):
    text = ""
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()
    return text

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

def send_to_openai(cv_content, criteria):

    prompt = f"""
    Resume Content:
    {cv_content}

    Criteria:
    {criteria}

    For each criteria, say satisfied or unsatisfied.
    Separate points with ';'.
    """

    if not client:
        return "AI service is temporarily unavailable. Please try later."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are an expert HR evaluator."},
            {"role": "user", "content": prompt}
        ]
    )

    return response.choices[0].message.content.strip()


def split_response(response):
    # Split the response by semicolon and strip extra spaces from each point
    points = [point.strip() for point in response.split(';')]
    return points

def feature2(request):
    context = {}
    if request.method == 'POST' and request.FILES.get('file') and request.POST.get('textbox'):
        # messages.success(request, 'Processing your data. Please wait...')
        uploaded_file = request.FILES['file']
        criteria = request.POST['textbox'] 
        
        fs = FileSystemStorage()
        filename = fs.save(uploaded_file.name, uploaded_file)
        file_path = fs.path(filename) 

        cv_content = extract_cv_content(file_path)

        response = send_to_openai(cv_content, criteria)

        context['response_text'] = split_response(response)

    return render(request, 'feature2.html', context)
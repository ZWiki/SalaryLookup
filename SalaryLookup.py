'''
Created on Oct 3, 2015

@author: chris wilkerson
'''


from os import linesep
import re
import tempfile
import subprocess

employees = []

class Employee:
    def __init__(self):
        pass
        
    def set_first_name(self, first_name):
        self.first_name = first_name

    def set_last_name(self, last_name):
        self.last_name = last_name
        
    def set_title(self, title):
        self.title = title
    
    def set_department(self, department):
        self.department = department
        
    def set_ibs(self, ibs):
        self.ibs = ibs
        
    def set_basis(self, basis):
        self.basis = basis
        
    def set_fte(self, fte):
        self.fte = fte
        
    def set_amt_ibs_gnrl(self, amt_ibs_gnrl):
        self.amt_ibs_gnrl = amt_ibs_gnrl

def pdf_to_text(pdf_file):
    f = open(pdf_file, 'rb')
    out_tf = tempfile.NamedTemporaryFile()
    subprocess.Popen(['pdftotext', '-layout', f.name, out_tf.name]).communicate()
    out_tf.seek(0)
    return out_tf.read()

def build_employee_list(pdf_file):
    text = pdf_to_text(pdf_file)
    header = b'''.*?EMPLOYEE NAME.*?\(IBS\)\s+FUND.*?\n(?P<text>.*?)\n\x0c'''
    for page in re.finditer(header, text, re.MULTILINE | re.IGNORECASE | re.DOTALL):
        for row in page.group('text').decode('utf-8').split(linesep):
            e = Employee()
            # Replace multiple space characters (2 or more) with '::'... it will make
            # further parsing easier
            line = re.sub('''\s{2,}''', '::', row)
            cols = [x.strip() for x in line.split('::')]
            if len(cols) != 7:
                raise Exception('Parse Error: Unexpected number of columns found', row)
            [name, title, dept, ibs, basis, fte, amt_fte] = cols
            last_name, first_name = [x.strip() for x in name.split(',')]
            e.set_last_name(last_name)
            e.set_first_name(first_name)
            e.set_title(title)
            e.set_department(dept)
            e.set_ibs(float(ibs.replace(',', '')))
            # BASIS can contain fractions that are represented as n/d
            regex = '''(?P<int_val>\d+)\s+(?:(?P<numerator>\d+)/(?P<denominator>\d+))?'''
            match = re.match(regex, basis)
            if match is None:
                raise Exception('Parse Error with basis, no match found', row)
            int_val = match.group('int_val')
            if match.group('numerator') is not None:
                numerator = match.group('numerator')
                denominator = match.group('denominator')
            else:
                numerator = 1
                denominator = 1
            f_basis = float(int_val) + float(numerator)/float(denominator)
            e.set_basis(f_basis)
            e.set_fte(float(fte))
            e.set_amt_ibs_gnrl(float(amt_fte.replace(',', '')))
            employees.append(e)
        
def get_employees_by_header(first_name=None, last_name=None, title=None, department=None):

    return [e for e in employees if\
        (e.title.lower() == title.lower() if title is not None else True) and\
        (e.department.lower() == department.lower() if department is not None else True) and\
        (e.first_name.lower() == first_name.lower() if first_name is not None else True) and\
        (e.last_name.lower() == last_name.lower() if last_name is not None else True)
    ]
    
def get_average_salary_by_header(title=None, department=None, inflate_to_12_months=False):
    l = get_employees_by_header(title=title, department=department)
    sum_salaries = sum([e.ibs if not inflate_to_12_months else (e.ibs*(12.0/e.basis)) for e in l])
    return round(sum_salaries / len(l), 2)
    
            
if __name__ == '__main__':
    build_employee_list('salaries2015.pdf')
    depts = set([e.department for e in employees])
        
    
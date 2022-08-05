# Copyright (c) 2022 Jean-René Robin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import datetime
import glob
from locale import currency
from re import A
import img2pdf
import json
import os
import PIL
import pdfkit
import random
import shutil
import sys
import time
import warnings

from faker import Faker
from jinja2 import Environment, FileSystemLoader
from pdf2image import convert_from_path
from PIL import Image
from typing import List

# Warnings disabled
warnings.simplefilter('ignore', Image.DecompressionBombWarning)

# Classes

class DatetimeEncoder(json.JSONEncoder):
    """
    Handle date in debug dump
    """
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

class CommandLineSettings:
    """
    Describes all the settings used for a command line execution of the script.
    """
    def __init__(self, out_dir: str, defects: bool, keep_original: bool, batch_size: int, statistics: bool, out_metadata:bool, locales_list: List[str]):
        self.out_dir = out_dir
        self.defects = defects
        self.keep_original = keep_original
        self.batch_size = batch_size
        self.statistics = statistics
        self.out_metadata = out_metadata
        self.locales_list = locales_list
        self.fakes_list = [Faker(x) for x in locales_list]

    def __str__(self):
        """
        Displays the class as a JSON string. Used for debug purposes.
        """
        output = {}

        output["out_dir"] = self.out_dir
        output["defects"] = self.defects
        output["keep_original"] = self.keep_original
        output["batch_size"] = self.batch_size
        output["statistics"] = self.statistics
        output["locale"] = self.locales_list
        output["out_metadata"] = self.locales_list

        return json.dumps(output, indent=4, sort_keys=True)

# Methods

def generate_invoice_data(commandLineSettings: CommandLineSettings):
    """
    Generate all data required for one invoice. Data generated may be not fully used by the invoices, 
    according to its template.
    """

    # Choose a random faker objet among those passed via command line.
    fake = random.choice(commandLineSettings.fakes_list)

    invoice_data = {}

    invoice_data["logo"] = generate_logo()
    invoice_data["supplier"] = generate_actor(fake=fake)
    invoice_data["client"] = generate_actor(fake=fake)
    invoice_data["order"] = generate_order(fake=fake)
    invoice_data["total"] = generate_total(fake=fake, order=invoice_data["order"])
    invoice_data["metadata"] = generate_metadata(fake=fake)
    invoice_data["file_name"] = "invoice-%s"%time.strftime('%Y%m%dT%H:%M:%S')
    
    if commandLineSettings.out_metadata:
        with open("%s/%s.json"%(commandLineSettings.out_dir, invoice_data["file_name"]), "w") as outfile:
            json.dump(invoice_data, outfile, indent=4, sort_keys=True, cls=DatetimeEncoder)

    return invoice_data

def generate_actor(fake: Faker):
    """
    Generate all data related to the supplier, who emits the invoices
    """

    actor = fake.profile()
    
    # remove some fields
    actor.pop("birthdate")
    actor.pop("current_location")
    actor.pop("blood_group")
    actor.pop("residence")
    actor.pop("sex")

    # add fields
    actor["company"] = fake.company()
    actor["catch_phrase"] = fake.catch_phrase()
    actor["phone_number"] = fake.phone_number()

    # handle country
    if fake.locales[0] == "de_DE":
        actor["country"] = "Deutschland"
    elif fake.locales[0] == "fr_FR":
        actor["country"] = "France"
    elif fake.locales[0] == "en_EN":
        actor["country"] = "United Kingdom"
    elif fake.locales[0] == "es_ES":
        actor["country"] = "España"
    else:
        actor["country"] = fake.country()

    # rewrite fields
    actor["mail"] = actor["name"].replace(" ", "-").lower() + "@" + fake.free_email_domain()

    return actor

def generate_order(fake: Faker):
    """
    Generate all data related to the order
    """

    order = []

    for i in range(0,random.randint(4,10)):
        item = {}
        item["name"] = fake.text(max_nb_chars=20)
        item["description"] = fake.text(max_nb_chars=60)
        item["unit_cost"] = random.uniform(.5, 75.5)
        item["quantity"] = random.randint(1,6)
        item["id"] = fake.ean(length=13)
        order.append(item)

    return order

def generate_total(fake: Faker, order):
    """
    Generate total sums using order data
    """

    total = {}

    # Misc
    total["paid"] = random.choice([False, True])
    total["currency"] = generate_currency(fake.locales[0])

    # Sub total of orders cost
    total["sub_total"] = 0.0
    for item in order:
        total["sub_total"] += item["unit_cost"] * item["quantity"]
    
    # Credit : Create an random, positive amount of credit the client have on his account
    total["credit"] = random.uniform(0,0.8) * total["sub_total"]
        
    # Shipping : If shipping is included (random), we add a shipping cost, based on the total of the before tax
    total["is_shipping_included"] = random.choice([False, True])
    
    if total["is_shipping_included"]:
        total["shipping"] =  random.uniform(0.1,0.3) * total["sub_total"]
    else:
        total["shipping"] = 0

    # Discount : If discount is included (random), we choose an random discount rate, and add a discounted amount
    total["is_discount_included"] = random.choice([False, True])
    
    if total["is_discount_included"]:
        total["discount_rate"] = random.choice([1,2,5])
        total["discount"] =  total["discount_rate"] / 100 * total["sub_total"]
    else:
        total["discount"] = 0
    
    # Total before tax
    total["total_before_tax"] = total["sub_total"] - total["discount"] + total["shipping"]
    
    # Tax is chosen randomly
    total["tax_rate"] = tax_rate = random.choice([5,10,15,20])
    total["total_after_tax"] = total["total_before_tax"] + total["tax_rate"] / 100 * total["total_before_tax"]
    total["tax"] = total["total_after_tax"] - total["total_before_tax"]

    return total

def generate_logo():
    """
    Returns a random filename, chosen among the files of the given path.
    """
    files = os.listdir("templates/assets/images/png")
    index = random.randrange(0, len(files))
    return files[index]

def generate_currency(locale: str):
    """
    Generate a currency object, based on the locale if provided. If not, a random locale is returned.
    """

    dollar = {}
    dollar["locale"] = ["us_US"]
    dollar["name"] = "dollar"
    dollar["sign"] = "$"

    euro = {}
    euro["locale"] = ["fr_FR", "de_DE", "es_ES"]
    euro["name"] = "euro"
    euro["sign"] = "€"

    pound = {}
    pound["locale"] = ["en_GB"]
    pound["name"] = "pound"
    pound["sign"] = "£"

    currency_list = [dollar, euro, pound]

    currency = None

    if locale == None:
        currency = random.choice(currency_list)
    else:
        try:
            currency = [x for x in currency_list if locale in x["locale"]][0]
        except IndexError:
            currency = random.choice(currency_list)

    return currency
    
def generate_metadata(fake: Faker):

    metadata = {}

    metadata["date_paid"] = fake.past_date()
    metadata["date_sent"] = fake.past_date()
    metadata["date_edited"] = fake.past_date()
    metadata["date_due"] = fake.future_date()
    metadata["order_id"] = fake.ean(length=8)
    metadata["invoice_id"] = fake.localized_ean8()

    return metadata

def write_template(commandLineSettings: CommandLineSettings, invoice_data: dict):
    """
    Generate template
    """

    shutil.rmtree("%s/tmp"%commandLineSettings.out_dir, ignore_errors=True)
    os.makedirs(os.path.join(commandLineSettings.out_dir, "tmp"), exist_ok=True)

    # file names
    OUTFILE_HTML = "%s/tmp/%s.html"%(commandLineSettings.out_dir, invoice_data["file_name"])
    OUTFILE_PDF = "%s/%s.pdf"%(commandLineSettings.out_dir, invoice_data["file_name"])

    # Load our template
    environment = Environment(loader=FileSystemLoader("."))
    template = environment.get_template(random_template())

    # Generate content
    content = template.render(
        base_dir = os.getcwd(),
        invoice = invoice_data)

    # Generate HTML template
    with open(OUTFILE_HTML, mode="w", encoding="utf-8") as message:
            message.write(content)

    options = {'enable-local-file-access': True}
    pdfkit.from_file(OUTFILE_HTML, OUTFILE_PDF, options=options)

    shutil.rmtree("%s/tmp"%commandLineSettings.out_dir, ignore_errors=True)

    return OUTFILE_PDF

def add_defects(commandLineSettings: CommandLineSettings, file: str):
    """
    Alter the template, so it looks like a scanned document
    """

    shutil.rmtree("%s/tmp"%commandLineSettings.out_dir, ignore_errors=True)

    os.makedirs(os.path.join(commandLineSettings.out_dir, "tmp"), exist_ok=True)
    pdf_file = file

    # Convert PDF to images
    pages = convert_from_path(pdf_file, 500)
    
    altered_image_path = "%s/tmp/%s-defects.pdf"%(commandLineSettings.out_dir, time.time())

    page_index = 1
    pages_image_array = []

    for page in pages:
        page_image = "%s-%02d.png"%(os.path.splitext(altered_image_path)[0], page_index)
        page.save(page_image, 'PNG')
        page_index += 1
        pages_image_array.append(page_image)

    signature_path = random_signature()
    paper_overlay_path  = random_paper_overlay()
    grunge_overlay_path = random_grunge_overlay()
    resized_factor = random.choice([700,1000,1500,1800])

    page_index = 1
    for page_image in pages_image_array:
        
        base_image = Image.open(page_image).convert('RGB')

        # Operation : Add signature on last page
        if page_index == len(pages_image_array):
            
            start_time = time.time()

            # Load images
            signature_image = Image.open(signature_path).convert('RGBA')

            # Resize signature
            base_width = int(random.randint(20,33)/100 * base_image.size[0])
            width_percent = (base_width / float(signature_image.size[0]))
            horizontal_size = int((float(signature_image.size[1]) * float(width_percent)))
            signature_image = signature_image.resize((base_width, horizontal_size), PIL.Image.Resampling.LANCZOS)

            # Paste image with transparency
            base_image.paste(signature_image, (random.randint(0,base_image.size[0]-signature_image.size[0]), (random.randint(int(base_image.size[1]/4),base_image.size[1]-signature_image.size[1]))), signature_image)

            # Save image
            base_image.save(page_image)
            if commandLineSettings.statistics: print("  ⏲  Added signature in %.2f seconds." % (time.time() - start_time))

        # Operation : Merge images with altered paper textures
        start_time = time.time()

        # Load images
        base_image = Image.open(page_image).convert('RGB')
        paper_texture = Image.open(paper_overlay_path).convert('RGB')

        # Resize paper texture to the base image
        paper_texture_resized = paper_texture.resize(base_image.size)

        # alpha is 0.0, a copy of the first image is returned
        altered_image = Image.blend(base_image, paper_texture_resized, random.uniform(0.4,0.6))

        # Save image
        altered_image.save(page_image)
        if commandLineSettings.statistics: print("  ⏲  Added paper texture in %.2f seconds." % (time.time() - start_time))

        # Operation : Reduce image size
        start_time = time.time()

        # Load image
        base_image = Image.open(page_image).convert('RGB')

        # Assign random new width and reduce it
        base_width = resized_factor
        width_percent = (base_width / float(base_image.size[0]))
        horizontal_size = int((float(base_image.size[1]) * float(width_percent)))
        resized = base_image.resize((base_width, horizontal_size), PIL.Image.Resampling.LANCZOS)

        # Save image
        resized.save(page_image)
        if commandLineSettings.statistics: print("  ⏲  Reduced image size in %.2f seconds." % (time.time() - start_time))

        # Operation : Rotate image

        # Load image        
        base_image = Image.open(page_image).convert('RGB')
        
        # Rotate it by 45 degrees
        rotated = base_image.rotate(random.uniform(-2.0, 2.0), PIL.Image.Resampling.NEAREST , expand = 0, fillcolor = "white")

        # Save image
        rotated.save(page_image)

        # Operation : Add grunge
        start_time = time.time()
 
        # Load images
        base_image = Image.open(page_image).convert('RGB')
        grunge_texture = Image.open(grunge_overlay_path).convert('RGB')
        
        # Resize paper texture to the base image
        grunge_texture_resized = grunge_texture.resize(base_image.size)

        # alpha is 0.0, a copy of the first image is returned
        altered_image = Image.blend(base_image, grunge_texture_resized, random.uniform(0,0.25))

        altered_image.save(page_image)
        if commandLineSettings.statistics: print("  ⏲  Added grunge texture in %.2f seconds." % (time.time() - start_time))

        page_index += 1

    # Convert all images to a single PDF

    if commandLineSettings.keep_original:
        pdf_path = "%s-defects.pdf"%os.path.splitext(pdf_file)[0]
    else:
        pdf_path = pdf_file

    with open(pdf_path,"wb") as f:
        f.write(img2pdf.convert(sorted(glob.glob("%s/tmp/*.png"%commandLineSettings.out_dir))))

    # Delete
    shutil.rmtree("%s/tmp"%commandLineSettings.out_dir, ignore_errors=True)

def random_paper_overlay():
    """
    Return a random paper overlay
    """
    files = sorted(glob.glob("templates/textures/paper/*jpeg"))
    index = random.randrange(0, len(files))
    return files[index]

def random_grunge_overlay():
    """
    Return a random grunge overlay
    """
    files = sorted(glob.glob("templates/textures/grunge/*jpeg"))
    index = random.randrange(0, len(files))
    return files[index]

def random_signature():
    """
    Return a random signature
    """
    files = sorted(glob.glob("templates/textures/signature/*png"))
    index = random.randrange(0, len(files))
    return files[index]

def random_template():
    """
    Return a random template
    """
    files = sorted(glob.glob("templates/html/*html.j2"))
    index = random.randrange(0, len(files))
    
    return files[index]
    
def main():
    ap = argparse.ArgumentParser(description="A python script that generates fake invoices.")

    ap.add_argument("-o", "--out_dir", type=str, default='dist/',
                    help="Path to save generated invoices.")
    ap.add_argument("-d", "--defects", action='store_true', default=False,
                    help="Add defects to the generated invoices.")
    ap.add_argument("-m", "--metadata", action='store_true', default=False,
                    help="Save invoice metadata in JSON format.")
    ap.add_argument("-k", "--keep-original", action='store_true', default=False,
                    help="Used with --add-defects. Keep a copy of the original, clean PDF before degradation.")
    ap.add_argument("-b", "--batch-size", type=int, default=1,
                    help="Number of invoices generated")
    ap.add_argument("-s", "--statistics", action='store_true', default=False,
                    help="Display generation statistics")
    ap.add_argument('-l', '--locales-list', default=["en-GB"], nargs='+',
                    help="List of locales used to fake data. Faker support multiples locale, see https://faker.readthedocs.io/en/master/locales.html")

    args = ap.parse_args()

    commandLineSettings = CommandLineSettings(args.out_dir, args.defects, args.keep_original, args.batch_size, args.statistics, args.metadata, args.locales_list)

    # print(commandLineSettings)

    os.makedirs(os.path.join("dist"), exist_ok=True)

    for i in range (1, commandLineSettings.batch_size + 1):
        print("✨ Generating invoice %d/%d"%(i, commandLineSettings.batch_size))

        # Generate fake invoice data
        start_time = time.time()
        invoice_data = generate_invoice_data(commandLineSettings=commandLineSettings)
        if commandLineSettings.statistics: print("🧾 Generated invoice data in %.2f seconds." % (time.time() - start_time))

        # Create a PDF using the data
        start_time = time.time()
        OUTFILE_PDF = write_template(commandLineSettings= commandLineSettings, invoice_data = invoice_data)
        if commandLineSettings.statistics: print("📄 Generated PDF in %.2f seconds." % (time.time() - start_time))

        # Add defects to the PDF
        if commandLineSettings.defects:
            start_time = time.time()
            add_defects(commandLineSettings=commandLineSettings, file=OUTFILE_PDF)    
            if commandLineSettings.statistics: print("💥 Altered PDF in %.2f seconds." % (time.time() - start_time))

if __name__ == '__main__':
    main()

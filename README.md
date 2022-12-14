# invoices-dataset-generator

A python script that generates fake invoices.

![examples](public/examples.png?raw=true)

## Installation

The `setup.sh` script will install needed packages and python dependencies in a virtual environment. It supports macOs and Linux.

```bash
./setup.sh
```

## Usage

To be able to use the script, you need to source the virtual environment that the package was installed in :

```bash
source .venv/bin/activate`
```

```bash
usage: generate.py [-h] [-o OUT_DIR] [-d] [-m] [-k] [-b BATCH_SIZE] [-s] [-l LOCALES_LIST [LOCALES_LIST ...]]

A python script that generates fake invoices.

optional arguments:
  -h, --help            show this help message and exit
  -o OUT_DIR, --out_dir OUT_DIR
                        Path to save generated invoices.
  -d, --defects         Add defects to the generated invoices.
  -m, --metadata        Save invoice metadata in JSON format.
  -k, --keep-original   Used with --add-defects. Keep a copy of the original, clean PDF before degradation.
  -b BATCH_SIZE, --batch-size BATCH_SIZE
                        Number of invoices generated
  -s, --statistics      Display generation statistics
  -l LOCALES_LIST [LOCALES_LIST ...], --locales-list LOCALES_LIST [LOCALES_LIST ...]
                        List of locales used to fake data. Faker support multiples locale, see https://faker.readthedocs.io/en/master/locales.html
```

Basic usage : 
```
$ python generate.py -b 2
✨  Generating invoice 1/2
✨  Generating invoice 2/2
```

Use specific locales for fake data : 
```
$ python generate.py -l fr_FR de_DE en_GB es_ES -b 5
✨  Generating invoice 1/5
✨  Generating invoice 2/5
✨  Generating invoice 3/5
✨  Generating invoice 4/5
✨  Generating invoice 5/5
```

Add some defects : 
```
$ python generate.py -d
✨  Generating invoice 1/1
```

Extract metadata : The data used for building the template will be written in the output folder, in a JSON file.
```
$ python generate.py -m -b 2
✨  Generating invoice 1/2
✨  Generating invoice 2/2
```

The invoices will be created in the `./dist` folder, or in the folder you want, using the `-o` flag.

## Next
- [x] Publish on Github
- [ ] Add many more jinja2 templates, from real world examples
- [ ] Add more variations : PAID/UNPAID, stamps, different layout in the same template
- [ ] Try to train [naiveHobo/InvoiceNet](https://github.com/naiveHobo/InvoiceNet) with the output data


## Credit

### Templates 
- Bootdey.com - http://bootdey.com/license

## Licence

MIT
# invoice-dataset-generator

A python script that generates fake invoices.



## Installation

The `setup.sh` script will install needed packages and python dependencies in a virtual environment. It supports macOs and Linux.

```bash
./setup.sh
```

## Usage

All commands must me 

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

```
$ python generate.py -b 2                                                                                [19:17:01]
✍️  Generating invoice 1/2
✍️  Generating invoice 2/2
```

## Credit

### Templates 
- Bootdey.com - http://bootdey.com/license

## Licence

MIT
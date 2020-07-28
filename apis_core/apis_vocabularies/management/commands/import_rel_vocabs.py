import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand

cwd = settings.BASE_DIR


def create_vocab_item(vocab_class, row, row_key):
    """gets or create a vocab entry based on name and name_reverse"""
    try:
        name_reverse = row[row_key].split("|")[1]
        name = row[row_key].split("|")[0]
    except IndexError:
        name_reverse = row[row_key]
        name = row[row_key]
    temp_item, _ = vocab_class.objects.get_or_create(
        name=name, name_reverse=name_reverse
    )
    return temp_item


class Command(BaseCommand):
    # Show this when the user types help
    help = "creates vocab entries (for relations) stored in the passed in Excel-Sheet"

    def add_arguments(self, parser):
        parser.add_argument('data', type=str, help='Location of your Excel-Sheet')

    # A command must define handle()
    def handle(self, *args, **kwargs):
        file = kwargs['data']
        excel_book = pd.read_excel(file, None)
        for x in excel_book.keys():
            df = pd.read_excel(file, x)
            col_len = len(df.columns)
            for i, row in df.iterrows():
                c = 1
                vocab_class = eval(x)
                while c <= col_len:
                    row_key = "ebene_{}".format(c)
                    if isinstance(row[row_key], str):
                        temp_item = create_vocab_item(vocab_class, row, row_key)
                        if c > 1:
                            parent_key = "ebene_{}".format(c-1)
                            parent = create_vocab_item(vocab_class, row, parent_key)
                            temp_item.parent_class = parent
                            temp_item.save()
                            self.stdout.write("{} crated/updated".format(temp_item))
                    c += 1

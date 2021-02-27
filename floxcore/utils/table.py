from dataclasses import asdict

import click
from terminaltables import SingleTable

from floxcore.exceptions import FloxException


class TableException(FloxException):
    pass


class BaseTable(SingleTable):
    def __init__(self, data):
        super().__init__(data)

        self.inner_row_border = False
        self.inner_column_border = False
        self.outer_border = False
        self.inner_heading_row_border = True

    def show(self):
        click.echo("")
        click.echo(self.table)
        click.echo("")


class DataObjectTable(BaseTable):
    def __init__(self, data, do=None, hide=None):
        if not any([data, do]):
            raise TableException("You need to provide either data or DataObject class to create Table")

        obj = do or type(next(iter(data)))

        header = list(obj.__annotations__.keys())
        if hide:
            header = list(filter(lambda x: x not in hide, header))

        filtered_data = []
        for row in data:
            row = asdict(row)
            if hide:
                row = [v for k, v in row.items() if k not in hide]
            else:
                row = row.values()

            filtered_data.append(row)

        super().__init__([header] + filtered_data)

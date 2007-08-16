from django.core.management.base import LabelCommand

class Command(LabelCommand):
    help = "Creates the table needed to use the SQL cache backend."
    args = "[tablename]"
    label = 'tablename'

    requires_model_validation = False

    def handle_label(self, tablename, **options):
        from django.db import backend, connection, transaction, models
        fields = (
            # "key" is a reserved word in MySQL, so use "cache_key" instead.
            models.CharField(name='cache_key', max_length=255, unique=True, primary_key=True),
            models.TextField(name='value'),
            models.DateTimeField(name='expires', db_index=True),
        )
        table_output = []
        index_output = []
        for f in fields:
            field_output = [backend.quote_name(f.name), f.db_type()]
            field_output.append("%sNULL" % (not f.null and "NOT " or ""))
            if f.unique:
                field_output.append("UNIQUE")
            if f.primary_key:
                field_output.append("PRIMARY KEY")
            if f.db_index:
                unique = f.unique and "UNIQUE " or ""
                index_output.append("CREATE %sINDEX %s_%s ON %s (%s);" % \
                    (unique, tablename, f.name, backend.quote_name(tablename),
                    backend.quote_name(f.name)))
            table_output.append(" ".join(field_output))
        full_statement = ["CREATE TABLE %s (" % backend.quote_name(tablename)]
        for i, line in enumerate(table_output):
            full_statement.append('    %s%s' % (line, i < len(table_output)-1 and ',' or ''))
        full_statement.append(');')
        curs = connection.cursor()
        curs.execute("\n".join(full_statement))
        for statement in index_output:
            curs.execute(statement)
        transaction.commit_unless_managed()

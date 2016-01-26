import csv
from collections import namedtuple

def clean_value(val):
    try:
        return int(val)
    except ValueError:
        return val.replace("\\n", "\n")

# Load a database file (equivalent of treasurebox arks)
# For runtime-computed parameters, pass a function into kwargs
# for the attribute name you want, the function will be called
# with the loaded object, and the result added under the kwarg name.
# This is particularly useful for joining multiple DBs with a
# foreign-key relationship.

# Ex. >>> data = load_db_file("some.csv", myattr=lambda raw: raw.id + 1)
#     >>> print(data[0])
#     (id=0, myattr=1)
def load_db_file(file, **kwargs):
    class_name = file.split("/")[-1].rsplit(".", 1)[0] + "_t"

    with open(file, "r") as cin:
        reader = csv.reader(cin)
        fields = next(reader)
        raw_field_len = len(fields)
        # print(fields)
        the_raw_type = namedtuple("_" + class_name, fields)

        keys = list(kwargs.keys())
        for key in keys:
            fields.append(key)

        the_type = namedtuple(class_name, fields)

        for val_list in filter(lambda list: len(list) == raw_field_len, reader):
            temp_obj = the_raw_type(*map(clean_value, val_list))
            try:
                extvalues = tuple(kwargs[key](temp_obj) for key in keys)
            except Exception:
                raise RuntimeError(
                    "Uncaught exception while filling stage2 data for {0}. Are you missing data?".format(temp_obj))
            yield the_type(*temp_obj + extvalues)

# Load a database file, and return a dict keyed by the content of the
# key_col parameter. This performs the same runtime-computing as
# load_db_file.

# Ex. >>> data = load_keyed_db_file("some.csv")
#     >>> print(data[0])
#     (id=13, another_column="string")
#     >>> print(data)
#     {13: (id=13, another_column="string")}
def load_keyed_db_file(file, key_col=0, **kwargs):
    ret_dic = {}
    tab = load_db_file(file, **kwargs)
    for thing in tab:
        ret_dic[thing[0]] = thing

    return ret_dic

if __name__ == "__main__":
    import sys
    want_keys = sys.argv[2:]
    file = sys.argv[1]
    for entry in load_db_file(file):
        print(*(getattr(entry, key) for key in want_keys))

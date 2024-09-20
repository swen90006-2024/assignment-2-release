# Implement your grammar here in the `grammar` variable.
# You may define additional functions, e.g. for generators.
# You may not import any other modules written by yourself.
# That is, your entire implementation must be in `grammar.py`
# and `fuzzer.py`.

grammar = {
    "<start>":            ["<create_table>"],
    "<create_table>":     ["CREATE TABLE <table_name> (<table_columns_def>);"],
    "<table_name>":       ["<string>"],
    "<table_columns_def>":["<table_column_def>",
                        "<table_columns_def>,<table_column_def>"],
    "<table_column_def>": ["<string> TEXT"],
    "<string>":           ["<letter>", "<letter><string>"],
    "<letter>":           ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k",
                        "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v",
                        "w", "x", "y", "z"]
}

# Code is copied/modified from https://jzamudio.com/sql-grammar-based-fuzzer/

from fuzzingbook.GrammarFuzzer import EvenFasterGrammarFuzzer
import grammar

class MyGrammarFuzzer:
    def __init__(self):
        # This function must not be changed.
        self.grammar = grammar.grammar
        self.setup_fuzzer()
    
    def setup_fuzzer(self):
        # This function may be changed.
        self.fuzzer = EvenFasterGrammarFuzzer(self.grammar)

    def fuzz(self) -> str:
        # This function may be changed, but the signature should not change.
        return self.fuzzer.fuzz()

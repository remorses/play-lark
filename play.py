from collections import defaultdict
from toposort import toposort, toposort_flatten
from lark import Lark, Tree, Transformer
from lark.indenter import Indenter
from orderedset import OrderedSet

tree_grammar = r"""
    start: _NL* tree
    tree: NAME _NL [_INDENT tree+ _DEDENT]
    %import common.CNAME -> NAME
    %import common.WS_INLINE
    %declare _INDENT _DEDENT
    %ignore WS_INLINE
    _NL: /(\r?\n[\t ]*)+/
"""


class TreeIndenter(Indenter):
    NL_type = "_NL"
    OPEN_PAREN_types: list = []
    CLOSE_PAREN_types: list = []
    INDENT_type = "_INDENT"
    DEDENT_type = "_DEDENT"
    tab_len = 8


parser = Lark(tree_grammar, parser="lalr", postlex=TreeIndenter())

test_tree = """
a
    b
    c
        d
        e
    f
        g
            x
                y
"""


class GetDependencies(Transformer):
    dependencies: defaultdict = defaultdict(OrderedSet)

    def start(self, children):
        ordered_deps = list(toposort_flatten(self.dependencies_as_sets))
        for k in ordered_deps:
            v = self.dependencies[k]
            to_process = [x for x in v if x in self.dependencies]
            for x in to_process:
                self.dependencies[k].update(self.dependencies[x])
        return Tree("start", children)

    @property
    def dependencies_as_sets(self,):
        return {k: set(v) for k, v in self.dependencies.items()}

    def tree(self, children):
        if not children:
            return Tree("tree", [])
        this = str(children[0])
        for child in children[1:]:
            name = child.children[0]
            self.dependencies[str(name)].add(this)
        return Tree("tree", children)


def test():
    t: Tree = parser.parse(test_tree)
    print(t.pretty())
    # l = t.iter_subtrees_topdown()
    # l = list(l)
    # for x in l:
    #     print('_')
    #     print(x.pretty())
    s = GetDependencies()
    t = s.transform(t)
    print(t.pretty())
    print(s.dependencies["e"])
    print(list(toposort(s.dependencies_as_sets)))


if __name__ == "__main__":
    test()

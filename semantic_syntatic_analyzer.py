# -*- coding: utf-8 -*-
import sys
import ply.yacc as yacc
import ply.lex as lex
import pprint

# Importar a lista de tokens do analisador léxico
from lex_analyzer import tokens, find_column
from utils.tree import Tree


global_tree = []
expa_list = []


class Scope(object):
    root_scope = {'father': None, 'children': [], 'elements': [], 'for': False}
    actual_scope = root_scope


def new_scope():
    child_scope = {'father': Scope.actual_scope, 'children': [], 'elements': []}
    Scope.actual_scope['children'].append(child_scope)
    child_scope['for'] = Scope.actual_scope['for']
    Scope.actual_scope = child_scope


def end_scope():
    Scope.actual_scope = Scope.actual_scope['father']


def find_var(name, scope):
    for e in scope['elements']:
        if e['name'] == name:
            return e
    if scope['father'] is None:
        return None
    return find_var(name, scope['father'])


def semantic_error(reason, p):
    print("Semantic error in input!", reason)
    for stack_element in p.stack[::-1]:
        if isinstance(stack_element, lex.LexToken):
            print("Line: %s, Column: %s" % (stack_element.lineno,
                                            find_column(p.lexer.lexdata, stack_element)))
            break;
    exit(-1)


def tree_type(tree):
    tl = tr = None

    if type(tree) is not Tree:
        var_type = type(tree)
        if var_type == float:
            return 'float'

        if var_type == int:
            return 'int'

        if tree == 'null':
            return 'null'

        if type(tree) == str and tree[0] == '"':
            return 'string'

        if type(tree) == str:
            identifier = find_var(tree, Scope.actual_scope)
            return identifier['type']

    if tree.left is not None and type(tree.left) == Tree and tree.left.name == 'array':
        if tree_type(tree.left) == 'int':
            identifier = find_var(tree.name, Scope.actual_scope)
            return identifier['type']
        return None

    if tree.left is not None:
        tl = tree_type(tree.left)

    if tree.right is not None:
        tr = tree_type(tree.right)

    if tl is not None and tl == tr:
        return tl

    if tr is None:
        return tl

    return -1


# Define a regra inicial, por padrão o PLY irá usar a primeira regra definida
def p_program(p):
    """program : statement
                | funclist
                | epsilon
    """
    global_tree.append(('program', p[1]))


#essas próximas regras são apenas semânticas, perceba pela cauda da regra ser vazia
def p_new_scope(p):
    """new_scope :"""
    new_scope()
    if Scope.actual_scope['for']:
        return

    try:
        i = -1
        while str(p[i]) != 'for':
            i -= 1

        Scope.actual_scope['for'] = True

    except AttributeError:
        pass


def p_end_scope(p):
    """end_scope :"""
    end_scope()


def p_check_break(p):
    """check_break :"""
    if not Scope.actual_scope['for']:
        semantic_error("Break without a For statement.", p)


def p_verify_decl(p):
    """verify_decl : """
    for element in Scope.actual_scope['elements']:
        # Verifica se já existe variável no escopo com o mesmo nome
        if element['name'] == p[-1]:
            semantic_error("Variable '{}' already declared in this scope.".format(element['name']), p)


# Define as regras restantes da linguagem
def p_statement(p):
    """statement : oneline
                    | LBRACES new_scope statelist end_scope RBRACES"""
    global_tree.append((tuple(['statement'] + p[1:])))


def p_scopestatement(p):
    """scopestatement :  new_scope oneline end_scope
                        | LBRACES new_scope statelist end_scope RBRACES
    """


def p_oneline(p):
    """oneline : vardecl SEMICOLON
                            | atribstat SEMICOLON
                            | printstat SEMICOLON
                            | readstat SEMICOLON
                            | returnstat SEMICOLON
                            | ifstat
                            | forstat
                            | BREAK SEMICOLON check_break
                            | SEMICOLON
    """

def p_funclist(p):
    """funclist : funcdef funclist
                | funcdef
    """
    global_tree.append(('funclist', p[1:]))


def p_funcdef(p):
    """funcdef : DEF IDENT LPAREN paramlist RPAREN LBRACES new_scope statelist end_scope RBRACES
    """
    global_tree.append(('funcdef', p[1]))


def p_paramlist(p):
    """paramlist : types IDENT paramlistiter
                | epsilon
    """
    Scope.actual_scope['elements'].append({'type': p[1], 'name': p[2]})
    global_tree.append(('paramlist', p[1:]))


def p_paramlistiter(p):
    """paramlistiter : COMMA types IDENT paramlistiter
                | epsilon
    """
    if len(p) == 5:
        Scope.actual_scope['elements'].append({'type': p[2], 'name': p[3]})
    global_tree.append(('paramlistiter', p[1:]))


# Define a regra vazia
def p_epsilon(p):
    """epsilon :"""
    global_tree.append(('epsilon'))


def p_vardecl(p):
    """vardecl : types IDENT verify_decl integer """

    Scope.actual_scope['elements'].append({'type': p[1], 'name': p[2]})
    global_tree.append(('vardecl', p[1], p[2], p[3]))


def p_types_int(p):
    """types : INT"""
    p[0] = p[1]
    global_tree.append(('type', p[1]))


def p_types_float(p):
    """types : FLOAT"""
    p[0] = p[1]
    global_tree.append(('type', p[1]))


def p_types_string(p):
    """types : STRING"""
    p[0] = p[1]
    global_tree.append(('type', p[1]))


def p_integer(p):
    """integer : LBRACKET INTCONST RBRACKET integer
            | epsilon
    """
    global_tree.append((tuple(['integer'] + p[1:])))


def p_atribstat(p):
    """atribstat : lvalue ATRIB expression
                    | lvalue ATRIB allocexpression
                    | lvalue ATRIB funccall
    """
    global_tree.append((tuple(['atribstat'] + p[1:])))


def p_funccall(p):
    """funccall : IDENT LPAREN paramlistcall RPAREN"""
    global_tree.append(('funccall', p[1], p[2], p[3], p[4]))


def p_paramlistcall(p):
    """paramlistcall : IDENT paramlistcalliter
                        | epsilon
    """
    global_tree.append(('paramlistcall', p[1:]))


def p_paramlistcalliter(p):
    """paramlistcalliter : COMMA IDENT paramlistcalliter
                        | epsilon
    """
    global_tree.append(('paramlistcall', p[1:]))


def p_printstat(p):
    """printstat : PRINT expression"""
    global_tree.append((tuple(['printstat'] + p[1:])))


def p_readstat(p):
    """readstat : READ lvalue"""
    global_tree.append((tuple(['readstat'] + p[1:])))


def p_returnstat(p):
    """returnstat : RETURN"""
    global_tree.append(('returnstat', p[1]))


def p_ifstat(p):
    """ifstat : IF LPAREN expression RPAREN scopestatement else"""
    global_tree.append((tuple(['ifstat'] + p[1:])))


def p_else(p):
    """else : ELSE scopestatement
            | epsilon
    """
    global_tree.append((tuple(['else'] + p[1:])))


def p_forstat(p):
    """forstat : FOR LPAREN atribstat SEMICOLON expression SEMICOLON atribstat RPAREN scopestatement"""
    global_tree.append((tuple(['forstat'] + p[1:])))


def p_statelist(p):
    """statelist : statement
                    | statement statelist
    """
    global_tree.append((tuple(['statelist'] + p[1:])))


def p_allocexpression(p):
    """allocexpression : NEW types numexpressions"""
    global_tree.append((tuple(['allocexpression'] + p[1:])))


def p_numexpressions(p):
    """numexpressions : LBRACKET numexpression RBRACKET numexpressions
                    | LBRACKET numexpression RBRACKET
    """
    if len(p) == 5:
        p[0] = Tree("array", p[2], p[4])
    else:
        p[0] = Tree("array", p[2])
    global_tree.append((tuple(['numexpressions'] + p[1:])))


def p_expression(p):
    """expression : numexpression
                    | binaryoperator numexpression
    """
    index = 1
    if len(p) == 3:
        index = 2
        if tree_type(p[1]) != tree_type(p[2]):
            semantic_error("Type mismatch", p)

    if tree_type(p[index]) == -1:
        semantic_error("Type mismatch", p)
    expa_list.append(p[index])
    global_tree.append((tuple(['expression'] + p[1:])))


def p_binaryoperator(p):
    """binaryoperator : numexpression relationaloperator
                        | epsilon
    """
    p[0] = p[1]
    global_tree.append((tuple(['binaryoperator'] + p[1:])))


def p_relationaloperator(p):
    """relationaloperator : RELOP"""
    global_tree.append(('relationaloperator', p[1]))


def p_numexpression(p):
    """numexpression : term signedterms"""
    if p[2] is None:
        p[0] = p[1]
    else:
        p[2].left = p[1]
        p[0] = p[2]
    global_tree.append((tuple(['numexpression'] + p[1:])))


def p_signedterms(p):
    """signedterms : signal term signedterms
                    | epsilon
    """
    if len(p) == 4:
        if p[3] is None:
            p[0] = Tree(p[1], None, p[2])
        else:
            p[3].left = p[2]
            p[0] = Tree(p[1], None, p[3])
    global_tree.append((tuple(['signedterms'] + p[1:])))


def p_signal(p):
    """signal : SIGNAL"""
    p[0] = p[1]
    global_tree.append(('signal', p[1]))


def p_term(p):
    """term : unaryexpr unaryiter"""
    if p[2] is not None:
        p[2].left = p[1]
        p[0] = p[2]
    else:
        p[0] = p[1]
    global_tree.append((tuple(['term'] + p[1:])))


def p_unaryiter(p):
    """unaryiter : unaryop unaryexpr unaryiter
                    | epsilon
    """
    if len(p) == 4:
        if p[3] is None:
            p[0] = Tree(p[1], None, p[2])
        else:
            p[3].left = p[2]
            p[0] = Tree(p[1], None, p[3])
    global_tree.append((tuple(['unaryiter'] + p[1:])))


def p_unaryop(p):
    """unaryop : UNARYOP"""
    p[0] = p[1]
    global_tree.append(('unaryop', p[1]))


def p_unaryexpr(p):
    """unaryexpr : signal factor
                    | factor
    """
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Tree(p[1], p[2])
    global_tree.append((tuple(['unaryexpr'] + p[1:])))


def p_factor(p):
    """factor : INTCONST
                | FLOATCONST
                | STRCONST
                | NULL
                | lvalue
                | LPAREN numexpression RPAREN
    """
    if len(p) == 4: #se for parenteses conecta essa sub-árvore como filho
        p[0] = p[2]
    else:
        p[0] = p[1]
    global_tree.append((tuple(['factor'] + p[1:])))


def p_lvalue(p):
    """lvalue : IDENT
                | IDENT numexpressions
    """
    if find_var(p[1], Scope.actual_scope) is None:
        semantic_error("variable \'{}\' not declared.".format(p[1]), p)

    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = Tree(p[1], p[2])
    global_tree.append((tuple(['lvalue'] + p[1:])))


# Função de erro para erros sintáticos
def p_error(p):
    print("Syntax error in input! Token: %s" % (p,))
    print("Line: %s, Column: %s" % (p.lineno, find_column(p.lexer.lexdata, p)-1))

    if len(global_tree) == 0:
        print("Error production: %s" % (parser.productions[1],))
    else:
        print("Error production: %s" % (global_tree[-1],))
        for prod in parser.productions:
            if prod.name == global_tree[-1][0]:
                print(prod)
                break

    exit(1)


# Inicializa o analisador sintático
parser = yacc.yacc()

# Constrói o analisador sintático


def build_parser(program):
    with open(program, 'r') as target_file:
        return parser.parse(target_file.read())

#[[1], ['+', ['-', 2], ['+', [3]]]]
if __name__ == "__main__":
    l_tree = build_parser(sys.argv[1])
    print("Success! All arithmetic expressions contain only valid types")
    print("Success! All Variables declared correctly in scope")
    print("Success! No break statement outside of a loop")
    print("Symbol table:")
    pprint.pprint(Scope.actual_scope)
    print("Syntax Tree:")
    print(expa_list)
    print("Compilation Successful!")
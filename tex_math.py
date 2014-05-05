#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import subprocess
import sys
import unittest

COMMAND_PREFIX = 'gettextmath'

def generate_command_call(name, prefix, *args):
    return '\\' + prefix + name + '{' + '}{'.join(args) + '}'

class Parser:
    class Token:
        function = False
        def process(self, stack, output):
            output.append(self)

        def consume(self, stack):
            stack.append(self)

        def __repr__(self):
            return str(self)

    class Number(Token):
        def __init__(self, number):
            self.number = int(number)

        def generate(self):
            return str(self.number)

        def __eq__(self, other):
            return isinstance(other, Parser.Number) and self.number == other.number

        def __str__(self):
            return 'Number({})'.format(self.number)

    class Identifier(Token):
        def __init__(self, identifier):
            self.identifier = identifier

        def generate(self):
            return self.identifier

        def __eq__(self, other):
            return isinstance(other, Parser.Identifier) and self.identifier == other.identifier

        def __str__(self):
            return 'Identifier("{}")'.format(self.identifier)

    class Operator(Token):
        function = True

        def __init__(self, operation):
            self.operation = operation

        def process(self, stack, output):
            while len(stack) > 0 and stack[len(stack)-1].priority < self.priority:
                output.append(stack.pop())
            stack.append(self)

        def __eq__(self, other):
            return type(self) == type(other) and self.operation == other.operation

        def __str__(self):
            return 'Operator("{}")'.format(self.operation)

    class BinaryOperator(Operator):
        def consume(self, stack):
            self.arg2 = stack.pop()
            self.arg1 = stack.pop()
            stack.append(self)

        def generate(self):
            return generate_command_call(self.command, COMMAND_PREFIX, self.arg1.generate(), self.arg2.generate())

    class OperatorEqual(BinaryOperator):
        priority = 7
        command = 'equal'

    class OperatorNotEqual(BinaryOperator):
        priority = 7
        command = 'notequal'

    class OperatorGreaterEqual(BinaryOperator):
        priority = 6
        command = 'greaterequal'

    class OperatorLesserEqual(BinaryOperator):
        priority = 6
        command = 'lesserequal'

    class OperatorGreaterThan(BinaryOperator):
        priority = 6
        command = 'greaterthan'

    class OperatorLesserThan(BinaryOperator):
        priority = 6
        command = 'lesserthan'

    class OperatorAnd(BinaryOperator):
        priority = 11
        command = 'and'

    class OperatorOr(BinaryOperator):
        priority = 12
        command = 'or'

    class OperatorModulo(BinaryOperator):
        priority = 3
        command = 'modulo'

    class OperatorTernaryStart(Operator):
        priority = 100
        function = False
        def consume(self, stack):
            self.arg_truefalse = stack.pop()
            self.arg_condition = stack.pop()
            if not isinstance(self.arg_truefalse, Parser.OperatorTernaryMiddle):
                raise Exception('Operator "?" must have matching ":", but "{}" found'.format(self.arg_truefalse))
            stack.append(self)

        def generate(self):
            return generate_command_call('ifthenelse', COMMAND_PREFIX, self.arg_condition.generate(), self.arg_truefalse.true.generate(), self.arg_truefalse.false.generate())

    class OperatorTernaryMiddle(Operator):
        priority = 100
        function = False
        def consume(self, stack):
            self.false = stack.pop()
            self.true = stack.pop()
            stack.append(self)

    class OpenParenthesis(Token):
        priority = 100
        def process(self, stack, output):
            stack.append(self)

        def __str__(self):
            return 'OpenParenthesis'

    class CloseParenthesis(Token):
        priority = 100
        def process(self, stack, output):
            while len(stack) > 0 and not isinstance(stack[len(stack)-1], Parser.OpenParenthesis):
                x = stack.pop()
                output.append(x)
            open = stack.pop()
            if not isinstance(open, Parser.OpenParenthesis):
                raise Exception('Could not find matching left parenthesis')
            if len(stack) > 0 and stack[len(stack)-1].function:
                output.append(stack.pop())

        def __str__(self):
            return 'CloseParenthesis'

    tokens = [
        # boolean operations
        (re.compile(r'^(==)'), OperatorEqual),
        (re.compile(r'^(!=)'), OperatorNotEqual),
        (re.compile(r'^(>=)'), OperatorGreaterEqual),
        (re.compile(r'^(<=)'), OperatorLesserEqual),
        (re.compile(r'^(>)'), OperatorGreaterThan),
        (re.compile(r'^(<)'), OperatorLesserThan),
        (re.compile(r'^(&&)'), OperatorAnd),
        (re.compile(r'^(\|\|)'), OperatorOr),
        (re.compile(r'^(\?)'), OperatorTernaryStart),
        (re.compile(r'^(:)'), OperatorTernaryMiddle),
        # arithmentic operations
        (re.compile(r'^(%)'), OperatorModulo),
        # parenthesis
        (re.compile(r'^\('), OpenParenthesis),
        (re.compile(r'^\)'), CloseParenthesis),
        # others
        (re.compile(r'^([0-9]+)'), Number),
        (re.compile(r'^([_A-Za-z][_A-Za-z0-9]*)'), Identifier),
        (re.compile(r'^\s+'), None),
    ]

    def __init__(self, source):
        self.source = source
        self.overriden_identifiers = {}

    def override_identifier(self, old_identifier, new_identifier):
        self.overriden_identifiers[old_identifier] = new_identifier

    def parse(self):
        source = self.source
        output = []
        stack = []
        while len(source) > 0:
            for i in self.tokens:
                m = i[0].match(source)
                if m:
                    break
            if not m:
                raise Exception('No token matches "{}<...>"'.format(source[:10]))

            source = source[len(m.group(0)):]
            token = i[1]
            if not token:
                continue
            args = m.groups()
            token = token(*args)
            token = token.process(stack, output)
        while len(stack) > 0:
            output.append(stack.pop())
        o = []
        for i in output:
            if isinstance(i, Parser.Identifier):
                o.append(Parser.Identifier(self.overriden_identifiers.get(i.identifier, i.identifier)))
            else:
                o.append(i)
        output = o
        return output

class Generator:
    def __init__(self, queue):
        self.queue = queue

    def generate(self):
        stack = []
        for i in self.queue:
            i.consume(stack)
        if len(stack) != 1:
            raise Exception('RPN processing problem, stack size is not 1 ({})'.format(repr(stack)))
        r = stack[0]
        r = r.generate()
        return r

def generate_command(name, source, new_command=True):
    s = '\\newcommand' if new_command else '\\renewcommand'
    s += '{'+name+'}[1]{'
    parser = Parser(source)
    parser.override_identifier('n', '#1')
    s += Generator(parser.parse()).generate()
    s += '}'
    return s

class TestMath(unittest.TestCase):
    def test_parser(self):
        exprs = [(
            '0',
            [Parser.Number(0),]
        ),(
            '1',
            [Parser.Number(1),]
        ),(
            '01',
            [Parser.Number(1),]
        ),(
            '0 1',
            [Parser.Number(0), Parser.Number(1)]
        ),(
            '0 == 1',
            [Parser.Number(0), Parser.Number(1), Parser.OperatorEqual('==')]
        ),(
            '0%2 == 1',
            [
                Parser.Number(0),
                Parser.Number(2),
                Parser.OperatorModulo('%'),
                Parser.Number(1),
                Parser.OperatorEqual('==')
            ]
        ),(
            '0 == 1%2',
            [
                Parser.Number(0),
                Parser.Number(1),
                Parser.Number(2),
                Parser.OperatorModulo('%'),
                Parser.OperatorEqual('==')
            ]
        ),(
            '0 ? 1 : 2',
            [
                Parser.Number(0),
                Parser.Number(1),
                Parser.Number(2),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?')
            ]
        ),(
            '3 ? 4 : 5 ? 1 : 2',
            [
                Parser.Number(3),
                Parser.Number(4),
                Parser.Number(5),
                Parser.Number(1),
                Parser.Number(2),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?'),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?')
            ]
        ),(
            '3%6 ? 4%7 : 5%8 ? 1%9 : 2%10',
            [
                Parser.Number(3),
                Parser.Number(6),
                Parser.OperatorModulo('%'),
                Parser.Number(4),
                Parser.Number(7),
                Parser.OperatorModulo('%'),
                Parser.Number(5),
                Parser.Number(8),
                Parser.OperatorModulo('%'),
                Parser.Number(1),
                Parser.Number(9),
                Parser.OperatorModulo('%'),
                Parser.Number(2),
                Parser.Number(10),
                Parser.OperatorModulo('%'),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?'),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?')
            ]
        ),(
            'n?0:a?1:2',
            [
                Parser.Identifier('n'),
                Parser.Number(0),
                Parser.Identifier('a'),
                Parser.Number(1),
                Parser.Number(2),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?'),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?')
            ]
        ),(
            'n?0:(a)?1:2',
            [
                Parser.Identifier('n'),
                Parser.Number(0),
                Parser.Identifier('a'),
                Parser.Number(1),
                Parser.Number(2),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?'),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?')
            ]
        ),(
            'n==1 ? 0 : (a || b) ? 1 : 2',
            [
                Parser.Identifier('n'),
                Parser.Number(1),
                Parser.OperatorEqual('=='),
                Parser.Number(0),
                Parser.Identifier('a'),
                Parser.Identifier('b'),
                Parser.OperatorOr('||'),
                Parser.Number(1),
                Parser.Number(2),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?'),
                Parser.OperatorTernaryMiddle(':'),
                Parser.OperatorTernaryStart('?')
            ]
        )]

        for i in exprs:
            parser = Parser(i[0])
            self.assertEqual(i[1], parser.parse(), 'expression parsed incorrectly: "{}"'.format(i[0]))

    def test_calculations(self):
        functions = [(
            '0',
            lambda n: 0
        ),(
            'n != 1',
            lambda n: int(n != 1)
        ),(
            'n>1',
            lambda n: int(n > 1)
        ),(
            'n>1 ? 1 : 0',
            lambda n: 1 if n > 1 else 0
        ),(
            'n==0 ? 10 : n==1 ? 11 : 12',
            lambda n: 10 if n == 0 else (11 if n == 1 else 12)
        ),(
            'n%10==1 && n%100!=11 ? 0 : n != 0 ? 1 : 2',
            lambda n: 0 if n%10 == 1 and n%100 != 11 else (1 if n != 0 else 2)
        ),(
            'n==1 ? 0 : n==2 ? 1 : 2',
            lambda n: 0 if n == 1 else (1 if n == 2 else 2)
        ),(
            'n==1 ? 0 : (n==0 || (n%100 > 0 && n%100 < 20)) ? 1 : 2',
            lambda n: 0 if n == 1 else (1 if (n == 0 or (n%100 > 0 and n%100 < 20)) else 2)
        ),(
            'n%10==1 && n%100!=11 ? 0 :  n%10>=2 && (n%100<10 || n%100>=20) ? 1 : 2',
            lambda n: 0 if n%10 == 1 and n%100 != 11 else (1 if n%10>=2 and (n%100<10 or n%100>=20) else 2)
        ),(
            'n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2',
            lambda n: 0 if n%10 == 1 and n%100 != 11 else (1 if n%10>=2 and n%10<=4 and (n%100<10 or n%100>=20) else 2)
        ),(
            '(n==1) ? 0 : (n>=2 && n<=4) ? 1 : 2',
            lambda n: 0 if n == 1 else (1 if n >= 2 and n <= 4 else 2)
        ),(
            'n==1 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2',
            lambda n: 0 if n == 1 else (1 if n%10 >= 2 and n%10 <= 4 and (n%100 < 10 or n%100 >= 20) else 2)
        ),(
            'n%100==1 ? 0 : n%100==2 ? 1 : n%100==3 || n%100==4 ? 2 : 3',
            lambda n: 0 if n%100 == 1 else (1 if n%100 == 2 else (2 if n%100 == 3 or n%100 == 4 else 3))
        )]

        re_text = re.compile(r'<text(.*?)>(.*?)</text>', re.DOTALL)
        re_tspan = re.compile(r'</?tspan(.*?)>', re.DOTALL)

        TEST_FILE_PREFIX = '_test'

        for i in functions:
            sys.stderr.write('*')
            sys.stderr.flush()
            for n in list(range(0,30))+list(range(40,300,10))+list(range(400,3000,100)):
                sys.stderr.write('.')
                sys.stderr.flush()
                with open(TEST_FILE_PREFIX+'.tex', 'w') as f:
                    f.write('\documentclass{article}\n')
                    f.write('\\usepackage{tipa}\n')
                    f.write('\\usepackage{gettext}\n')
                    f.write(generate_command('\\testfn', i[0]))
                    f.write('\n')
                    f.write('\\begin{document}\n')
                    f.write('\\testfn{''')
                    f.write(str(n))
                    f.write('}\n')
                    f.write('\\end{document}')
                kwargs = dict(stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.check_call(['latex', TEST_FILE_PREFIX+'.tex'], **kwargs)
                subprocess.check_call(['dvisvgm', TEST_FILE_PREFIX+'.dvi'], **kwargs)
                with open(TEST_FILE_PREFIX+'.svg') as f:
                    f = f.read()
                    f = f.replace('\n', '')
                    f = re_text.findall(f)
                    f = [ re_tspan.sub(' ', i[1]) for i in f ]
                    f = ''.join(f)
                    f = f.strip()
                    if f.endswith('1'): #strip page number
                        f = f[:-1]
                    f = f.strip()
                    f = int(f)

                expected = i[1](n)
                actual = f
                self.assertEqual(expected, actual)

if __name__ == '__main__':
    import unittest
    unittest.main()
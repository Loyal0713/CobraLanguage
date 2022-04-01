
import sys

from multipledispatch import dispatch

# operations
OPS = {"+": "ADD", "-": "SUB", "*": "MUL", "/": "DIV"}

# key words
KEYWORDS = {"if": "IF", "for": "FOR", "while": "WHILE", "print": "PRINT", "set": "SET", "cls": "CLS", "quit": "QUIT"}
INVALID_CHARS = ""
BREAK_CHARS = "(){}[]"

# assignments
SET = "SET"
ASSIGN = "ASSIGN"
ADD_ASSIGN = "ADD_ASSIGN"
SUB_ASSIGN = "SUB_ASSIGN"
MUL_ASSIGN = "MUL_ASSIGN"
DIV_ASSIGN = "DIV_ASSIGN"

# compare
EQU = "EQU"
GTE = "GTE"
LTE = "LTE"
GT = "GT"
LT = "LT"

# types
FLOAT = "FLOAT"
INT = "INT"
STR = "STR"
VAR = "VAR"

# braces
L_PAR = "L_PAR"
R_PAR = "R_PAR"
L_BKT = "L_BKT"
R_BKT = "R_BKT"
L_CUR = "L_CUR"
R_CUR = "R_CUR"

# idk
EOF = "EOF"

class DivideByZeroException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

class InvalidPeriodInNumberException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

class UnrecognizedCharException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

class MismatchTokenTypeException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

class InvalidCharInWord(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

class NotRecognizedCommandException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

class VariableUsedBeforeDeclared(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

class Token():
	type = None
	value = None

	def __init__(self, type, value):
		self.type = type
		self.value = value

	def __str__(self):
		return f"Token({self.type}, {self.value})"

	def __repr__(self):
		return self.__str__()

class Lexer:
	def __init__(self, text):
		self.text = text
		self.ptr = 0
		self.curr_char = self.text[self.ptr]

	# advance ptr and update current char
	def advance(self):
		self.ptr += 1
		if self.ptr > len(self.text) - 1:
			self.curr_char = None
		else:
			self.curr_char = self.text[self.ptr]

	# skip white space
	def skip_whitespace(self):
		while self.curr_char is not None and self.curr_char.isspace():
			self.advance()

	# generate number token from text, returns int if int, float if not
	def generate_num_token(self, isNegative):
		result = ""
		has_period = False
		while self.curr_char is not None and (self.curr_char.isdigit() or self.curr_char == "."):
			# check if there's a decimal point
			if self.curr_char == ".":
				if has_period:
					raise InvalidPeriodInNumberException("Too many periods in number")
				has_period = True
				result += self.curr_char
				self.advance()
			else:
				result += self.curr_char
				self.advance()

		if isNegative:
			result = float(result) * -1

		if has_period:
			return Token(FLOAT, float(result))
		else:
			return Token(INT, int(result))

	# generate operation token
	def generate_op_token(self):
		value = self.curr_char
		type = OPS[self.curr_char]
		self.advance()
		return Token(type, value)

	def generate_word(self):
		word = ""
		while self.curr_char is not None:
			if self.curr_char in INVALID_CHARS:
				raise InvalidCharInWord(f"Invalid char '{self.curr_char}' in word")
			if self.curr_char in OPS.keys():
				break
			if self.curr_char in BREAK_CHARS:
				break
			if self.curr_char == " ":
				break
			word += self.curr_char
			self.advance()

		# generate key word
		if word in KEYWORDS.keys():
			return Token(KEYWORDS[word], word)
		# generate var
		else:
			return Token(VAR, word)

	def generate_string(self):
		string = ""
		while self.curr_char is not None:
			if self.curr_char == "\"":
				self.advance()
				break
			string += self.curr_char
			self.advance()
		return Token(STR, string)

	# automatically gets the next token
	def get_next_token(self):
		while self.curr_char is not None:

			# skip whitespace
			if self.curr_char.isspace():
				self.skip_whitespace()
				continue

			# check if negative number or subracting
			if self.curr_char == "-":
				self.advance()
				if self.curr_char.isdigit():
					return self.generate_num_token(True)

			# generate number token?
			if self.curr_char.isdigit() or self.curr_char == ".":
				return self.generate_num_token(False)

			# generate op token?
			if self.curr_char in OPS.keys():
				return self.generate_op_token()

			# generate key word token?
			if self.curr_char.isalpha():
				return self.generate_word()

			# parentheses
			if self.curr_char == "(":
				self.advance()
				return Token(L_PAR, "(")
			if self.curr_char == ")":
				self.advance()
				return Token(R_PAR, ")")

			# square braces
			if self.curr_char == "[":
				self.advance()
				return Token(L_BKT, "[")
			if self.curr_char == "]":
				self.advance()
				return Token(R_BKT, "]")

			# curly brackets
			if self.curr_char == "{":
				self.advance()
				return Token(L_CUR, "{")
			if self.curr_char == "}":
				self.advance()
				return Token(R_CUR, "}")

			# assignments
			if self.curr_char == "=":
				self.advance()
				return Token(ASSIGN, "=")

			if self.curr_char == "\"":
				self.advance()
				return self.generate_string()

			raise UnrecognizedCharException(f"Cannot parse char: '{self.curr_char}'")

		return Token(EOF, None)

class Interpreter:
	vars = dict()
	def __init__(self, lexer):
		self.lexer = lexer
		self.curr_token = self.lexer.get_next_token()

	def eat(self, token_type):
		if self.curr_token.type == token_type:
			self.curr_token = self.lexer.get_next_token()
		else:
			raise MismatchTokenTypeException(f"Mismatch token type: {self.curr_token.type} != {token_type}")

	def factor(self):
		token = self.curr_token
		if token.type == STR:
			self.eat(token.type)
			return token.value

		if token.type == VAR:
			self.eat(token.type)
			result = ""
			try:
				result = self.vars[token.value]
			except KeyError:
				raise VariableUsedBeforeDeclared(f"Variable {token.value} used before declared")
			return result

		if token.type in ("FLOAT", "INT"):
			self.eat(token.type)
			return token.value
		elif token.type == L_PAR:
			self.eat(L_PAR)
			result = self.expr()
			self.eat(R_PAR)
			return result

	def term(self):
		result = self.factor()

		while self.curr_token.type in ("MUL", "DIV"):
			if self.curr_token.type == "MUL":
				self.eat(self.curr_token.type)
				result *= self.factor()
			elif self.curr_token.type == "DIV":
				self.eat(self.curr_token.type)
				# checks
				value = self.factor()
				if value == 0:
					raise DivideByZeroException("Cannot divide by zero")
				if result % value == 0:
					result = int(result / value)
				else:
					result /= value
		return result

	def assign_var(self):
		token = self.curr_token
		self.eat(SET)

		# var name
		var_name = self.curr_token.value
		self.eat(VAR)

		# assignment
		if self.curr_token.type == ASSIGN:
			self.eat(ASSIGN)

		# value
		value = self.curr_token.value
		self.eat(self.curr_token.type)

		# save var name and value
		self.vars[var_name] = value

	def script(self, isConsole):
		while self.curr_token.type != EOF:
			if self.curr_token.type == "PRINT":
				self.eat("PRINT")
				self.eat(L_PAR)
				result = self.expr()
				self.eat(R_PAR)
				print(result)
				continue

			if self.curr_token.type in ("INT", "FLOAT"):
				if isConsole:
					print(self.expr())

			if self.curr_token.type == "SET":
				self.assign_var()
				continue

			if self.curr_token.type == "CLS":
				self.eat("CLS")
				print("\033[H\033[J", end="")
				continue

			if self.curr_token.type == "QUIT":
				exit()

			if self.curr_token.value == None:
				continue

			raise NotRecognizedCommandException(f"Did not recoginize command: {self.curr_token.value}")

	def expr(self):
		result = self.term()
		while self.curr_token.type in ("ADD", "SUB"):
			if self.curr_token.type == "ADD":
				self.eat("ADD")
				result += self.term()
			elif self.curr_token.type == "SUB":
				self.eat("SUB")
				result -= self.term()
		return result

def console():
	while True:
		try:
			text = input("JB> ")
		except EOFError:
			break
		if not text:
			continue
		lexer = Lexer(text)
		interpreter = Interpreter(lexer)
		interpreter.script(True)

def get_file_contents(path):
	with open(path) as f:
		return f.read()

def main():

	if len(sys.argv) == 1:
		console()
	if len(sys.argv) == 2:
		script = get_file_contents(sys.argv[1])
		lexer = Lexer(script)
		interpreter = Interpreter(lexer)
		interpreter.script(False)

if __name__ == "__main__":
	main()

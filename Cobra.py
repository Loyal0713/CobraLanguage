
import sys

# data types
PRIMITIVES = ["FLOAT", "INT", "STRING", "NULL"]

# operations
# OPS = ["+", "-", "*", "/"]
OPS = "+-*/"

# braces
BRACES = { "(": "LPAR", ")": "RPAR", "{": "LCUR", "}": "RCUR", "[": "LBKT", "]": "RBKT" }

# keywords
KEYWORDS = ["IF", "FOR", "WHILE", "PRINT", "SET", "CLS", "QUIT"]

# comparisons
COMPARISONS = ["=", ">=", "<=", ">", "<"]

# invalid chars for vars or keywords
INVALID_CHARS = ""

EOF = "EOF"

# thrown when trying to divide by zero
class DivideByZeroException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

# thrown when there's two (or more) periods in number
class InvalidPeriodInNumberException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

# thrown when a char is not recognized by Tokenizer
class UnrecognizedCharException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

# thrown when token that is ate does not match current token type
class MismatchTokenTypeException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

# thrown when keyword is not recognized
class NotRecognizedKeywordException(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

# thrown when a variable is used before it's declared
class VariableUsedBeforeDeclared(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

# thrown when an invalid char is in the word, specifically for keywords and vars
class InvalidCharInWord(Exception):
	def __init__(self, message):
		self.message = message
		super().__init__(message)

# Token class containing the type of token and it's value
class Token:
	type = None
	value = None

	def __init__(self, type, value):
		self.type = type
		self.value = value

	def __str__(self):
		return f"Token({self.type}, {self.value})"

	def __repr__(self):
		return self.__str__()

# Tokenizer class that parses text and returns tokens
class Lexer:
	def __init__(self, text):
		self.text = text
		self.ptr = 0
		self.char = self.text[self.ptr]

	# advance pointer in text and update char, char set to None if end of text
	def advance(self):
		self.ptr += 1
		# reached end of text
		if self.ptr > len(self.text) - 1:
			self.char = None
		else:
			self.char = self.text[self.ptr]

	# skip whitespace
	def skip_whitespace(self):
		while self.char is not None and self.char.isspace():
			self.advance()

	# generates number token with support for negatives, floats, and ints
	def gen_num_token(self, isNegative):
		result = ""
		has_period = False

		# parse entire number
		while self.char is not None and (self.char.isdigit() or self.char == "."):
			# check for period
			if self.char == ".":
				if has_period:
					raise InvalidPeriodInNumberException("Too many periods in number")
				has_period = True
			result += self.char
			self.advance()

		# convert to negative if needed, return float or int
		if isNegative:
			result = float(result) * -1
		if has_period:
			return Token("FLOAT", float(result))
		else:
			return Token("INT", int(result))

	# generate operation token
	def gen_op_token(self):
		value = self.char
		self.advance()
		return Token("OP", value)

	# generate keyword or var token
	def gen_keyword_token(self):
		word = ""
		while self.char is not None:
			if self.char in INVALID_CHARS:
				raise InvalidCharInWord(f"Invalid char in word: '{self.char}'")
			if self.char in OPS:
				break
			if self.char == " ":
				break
			word += self.char
			self.advance()

		word = word.upper()

		# generate key words
		if word in KEYWORDS:
			return Token("KEYWORD", word)
		# generate var
		else:
			return("VAR", word)

	# generate string token
	def gen_string_token(self):
		word = ""
		while self.char is not None or self.char != "\"":
			word += self.char
			self.advance()
		return Token("STRING", word)

	# generate assignment token
	def gen_assign_token(self):
		return Token("ASSIGN", "=")

	def gen_brace_token(self):
		brace = self.curr
		self.advance()
		return Token(BRACES[brace], brace)

	# gets next token
	def get_next_token(self):
		while self.char is not None:

			# skip white space
			if self.char.isspace():
				self.skip_whitespace()
				continue

			# check for negative number or sub operation
			if self.char == "=":
				self.advance()
				if self.char.isdigit():
					return self.gen_num_token(True)

			# generate number token
			if self.char.isdigit() or self.char == ".":
				return self.gen_num_token(False)

			# generate operation token
			if self.char in OPS:
				return self.gen_op_token()

			# generate key word token or variable token
			if self.char.isalpha():
				return self.gen_keyword_token()

			# generate string token
			if self.char == "\"":
				self.advance()
				return self.gen_string_token()

			# generate assign token
			if self.char == "=":
				self.advance()
				return self.gen_assign_token()

			# generate brace token
			if self.char in BRACES.keys():
				return self.gen_brace_token()

			raise UnrecognizedCharException(f"Cannot parse char: '{self.char}'")

		return Token("EOF", None)

class Interpreter:
	# global vars are stored in here for now until scoping is implemented
	vars = dict()

	def __init__(self, lexer):
		self.lexer = lexer
		self.token = self.lexer.get_next_token()

	def eat(self, type):
		if self.token.type == type:
			self.token = self.lexer.get_next_token()
		else:
			raise MismatchTokenTypeException(f"Mismatch token types:\nCurr: {self.token.type}, Eating: {type}")

	def factor(self):
		token = self.token
		# string token type, return string value
		if token.type == "STRING":
			self.eat(token.type)
			return token.value

		# variable token type, attempt to return var value
		if token.type == "VAR":
			self.eat(token.type)
			result = ""
			try:
				result = self.vars[token.value]
			except KeyError:
				raise VariableUsedBeforeDeclared(f"Variable used before declared: {token.value}")
			return result

		# primitive token, return value
		if token.type in PRIMITIVES:
			self.eat(token.type)
			return token.value

		# token is "(", evaluate inside
		if token.type == "LPAR":
			self.eat("LPAR")
			result = self.expr()
			self.eat("RPAR")
			return result

	def term(self):
		result = self.factor()
		while self.token.type in ("MUL", "DIV"):

			# multiply
			if self.token.type == "MUL":
				self.eat(self.token.type)
				result *= self.factor()

			# divide
			if self.token.type == "DIV":
				self.eat(self.token.type)
				value = self.factor()

				# check for divide by zero
				if value == 0:
					raise DivideByZeroException("Cannot divide by zero")

				# check if return int
				if result % value == 0:
					result = int(result / value)
				else:
					result /= value

		return result

	# expression
	def expr(self):
		result = self.term()
		while self.token.type in ("ADD", "SUB"):
			# add
			if self.token.type == "ADD":
				self.eat("ADD")
				if type(result) is str:
					result = str(result)
					result += str(self.term())
				else:
					result += self.term()

			# sub
			if self.token.type == "SUB":
				self.eat("SUB")
				result -= self.term()

		return result

	def assign_var(self):
		self.eat("KEYWORD")
		var_name = self.token.value
		self.eat("VAR")
		self.eat("ASSIGN")
		value = self.token.value
		self.eat(self.token.value)
		self.vars[var_name] = value

	def script(self, isConsole):
		while self.token.type != EOF:
			if self.token.type == "PRINT":
				self.eat("PRINT")
				self.eat(L_PAR)
				result = self.expr()
				self.eat(R_PAR)
				print(result)
				continue

			if self.token.type in ("INT", "FLOAT"):
				if isConsole:
					print(self.expr())

			if self.token.type == "SET":
				self.assign_var()
				continue

			if self.token.type == "CLS":
				self.eat("CLS")
				print("\033[H\033[J", end="")
				continue

			if self.token.type == "QUIT":
				exit()

			if self.token.value == None:
				continue

			raise NotRecognizedCommandException(f"Did not recoginize command: {self.token.value}")

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

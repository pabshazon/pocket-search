from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
import ast
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import difflib
import torch
from enum import Enum


class EditType(Enum):
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    REFACTOR = "refactor"


@dataclass
class CodeEdit:
    edit_type: EditType
    location: Dict[str, int]  # line_number, column
    original_code: str
    modified_code: str
    confidence: float


class CodeEditor:
    def __init__(self, model_name: str = "Salesforce/codet5-base"):
        # Initialize tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

        # Set device
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.model.to(self.device)

    def parse_command(self, command: str) -> Dict[str, any]:
        """Parse natural language command to understand intent"""
        # Create prompt for intent classification
        prompt = f"Classify the edit type and location for: {command}"
        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate classification
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=50,
            num_return_sequences=1,
            temperature=0.3
        )

        # Decode and parse the classification
        classification = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Extract edit type and details
        if "add" in command.lower():
            edit_type = EditType.ADD
        elif "delete" in command.lower():
            edit_type = EditType.DELETE
        elif "refactor" in command.lower():
            edit_type = EditType.REFACTOR
        else:
            edit_type = EditType.MODIFY

        return {
            "edit_type": edit_type,
            "command": command
        }

    def locate_edit_position(self, code: str, command: Dict[str, any]) -> Dict[str, int]:
        """Determine the position in code where the edit should be made"""
        try:
            tree = ast.parse(code)

            # Find relevant node based on command
            target_node = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.name in command["command"].lower():
                        target_node = node
                        break

            if target_node:
                return {
                    "line_number": target_node.lineno,
                    "column": target_node.col_offset
                }

            # Default to end of file if no specific location found
            return {
                "line_number": len(code.splitlines()),
                "column": 0
            }

        except SyntaxError:
            # Handle incomplete or invalid code
            return {
                "line_number": 1,
                "column": 0
            }

    def generate_modification(self,
                              code: str,
                              command: Dict[str, any],
                              location: Dict[str, int]) -> str:
        """Generate code modification based on command"""
        # Create prompt for code generation
        prompt = f"""
        Original code:
        {code}

        Command: {command['command']}
        Location: Line {location['line_number']}

        Modified code:
        """

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.device)

        # Generate modified code
        outputs = self.model.generate(
            inputs["input_ids"],
            max_length=len(inputs["input_ids"][0]) + 200,
            num_return_sequences=1,
            temperature=0.7
        )

        modified_code = self.tokenizer.decode(outputs[0], skip_special_tokens=True)

        # Validate generated code
        try:
            ast.parse(modified_code)
            return modified_code
        except SyntaxError:
            # If generated code has syntax errors, try to fix or return original
            return self.fix_syntax_errors(modified_code)

    def fix_syntax_errors(self, code: str) -> str:
        """Attempt to fix common syntax errors in generated code"""
        # List of common syntax fixes
        fixes = [
            (r'[\t ]*\n[\t ]*\n+', '\n\n'),  # Fix multiple blank lines
            (r'\s+$', ''),  # Remove trailing whitespace
            (r'\(\s+\)', '()'),  # Fix empty parentheses
        ]

        fixed_code = code
        for pattern, replacement in fixes:
            import re
            fixed_code = re.sub(pattern, replacement, fixed_code)

        try:
            ast.parse(fixed_code)
            return fixed_code
        except SyntaxError:
            # If still invalid, return with comment
            return f"# Original code preserved due to syntax error in modification\n{code}"

    def calculate_confidence(self, original: str, modified: str) -> float:
        """Calculate confidence score for the modification"""
        if original == modified:
            return 0.0

        # Use difflib to calculate similarity
        similarity = difflib.SequenceMatcher(None, original, modified).ratio()

        # Adjust confidence based on similarity
        if similarity < 0.3:
            return 0.3  # Too different might mean error
        elif similarity > 0.9:
            return 0.9  # Too similar might mean minimal change
        else:
            return similarity

    def apply_edit(self, code: str, command: str) -> CodeEdit:
        """Main method to apply a code edit based on natural language command"""
        # Parse the command
        parsed_command = self.parse_command(command)

        # Find edit location
        location = self.locate_edit_position(code, parsed_command)

        # Generate modification
        modified_code = self.generate_modification(code, parsed_command, location)

        # Calculate confidence
        confidence = self.calculate_confidence(code, modified_code)

        return CodeEdit(
            edit_type=parsed_command["edit_type"],
            location=location,
            original_code=code,
            modified_code=modified_code,
            confidence=confidence
        )


# Example usage
def test_editor():
    editor = CodeEditor()

    original_code = """
def calculate_sum(numbers):
    return sum(numbers)
    """

    command = "Add input validation to check if numbers is empty"

    edit = editor.apply_edit(original_code, command)

    print(f"Original code:\n{edit.original_code}")
    print(f"\nModified code:\n{edit.modified_code}")
    print(f"\nConfidence: {edit.confidence}")
    print(f"Edit type: {edit.edit_type}")
    print(f"Location: {edit.location}")


if __name__ == "__main__":
    test_editor()
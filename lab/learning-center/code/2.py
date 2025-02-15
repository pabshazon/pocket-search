mport
ast
from typing import List, Dict, Set, Tuple
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    AutoModelForSeq2SeqLM,
    pipeline
)
import torch
import networkx as nx
from dataclasses import dataclass


@dataclass
class CodeAnalysis:
    dependencies: Dict[str, Set[str]]
    potential_bugs: List[Dict[str, str]]
    explanation: str
    documentation_refs: List[Dict[str, str]]


class CodeAnalyzer:
    def __init__(self):
        # Model for code understanding
        self.code_tokenizer = AutoTokenizer.from_pretrained("microsoft/codebert-base")
        self.code_model = AutoModelForSequenceClassification.from_pretrained("microsoft/codebert-base")

        # Model for natural language generation
        self.nlg_tokenizer = AutoTokenizer.from_pretrained("Salesforce/codet5-base")
        self.nlg_model = AutoModelForSeq2SeqLM.from_pretrained("Salesforce/codet5-base")

        # Set device
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
        elif torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.code_model.to(self.device)
        self.nlg_model.to(self.device)

        # Pipeline for code-to-text generation
        self.nlg_pipeline = pipeline(
            "text2text-generation",
            model=self.nlg_model,
            tokenizer=self.nlg_tokenizer,
            device=self.device
        )

    def extract_dependencies(self, code: str) -> Dict[str, Set[str]]:
        """Extract function and variable dependencies using AST"""
        dependencies = {
            'functions': set(),
            'variables': set(),
            'imports': set(),
            'calls': set()
        }

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    dependencies['functions'].add(node.name)
                elif isinstance(node, ast.Name):
                    if isinstance(node.ctx, ast.Store):
                        dependencies['variables'].add(node.id)
                elif isinstance(node, ast.Import):
                    for name in node.names:
                        dependencies['imports'].add(name.name)
                elif isinstance(node, ast.Call):
                    if hasattr(node.func, 'id'):
                        dependencies['calls'].add(node.func.id)

            # Build dependency graph
            self.dep_graph = nx.DiGraph()
            for func in dependencies['functions']:
                for call in dependencies['calls']:
                    if call in dependencies['functions']:
                        self.dep_graph.add_edge(func, call)

        except SyntaxError as e:
            return {'error': f'Syntax error in code: {str(e)}'}

        return dependencies

    def identify_bugs(self, code: str) -> List[Dict[str, str]]:
        """Identify potential bugs and improvement areas"""
        bugs = []

        try:
            tree = ast.parse(code)

            # Check for common issues
            for node in ast.walk(tree):
                # Check for bare except clauses
                if isinstance(node, ast.ExceptHandler) and node.type is None:
                    bugs.append({
                        'type': 'bare_except',
                        'line': node.lineno,
                        'message': 'Avoid using bare except clauses'
                    })

                # Check for mutable default arguments
                if isinstance(node, ast.FunctionDef):
                    for default in node.args.defaults:
                        if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                            bugs.append({
                                'type': 'mutable_default',
                                'line': node.lineno,
                                'message': f'Mutable default argument in function {node.name}'
                            })

                # Check for unused variables
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if not any(isinstance(parent, (ast.For, ast.FunctionDef))
                               for parent in ast.walk(tree)):
                        bugs.append({
                            'type': 'unused_variable',
                            'line': node.lineno,
                            'message': f'Potentially unused variable: {node.id}'
                        })

        except SyntaxError as e:
            bugs.append({
                'type': 'syntax_error',
                'line': e.lineno,
                'message': str(e)
            })

        return bugs

    def generate_explanation(self, code: str) -> str:
        """Generate natural language explanation of the code"""
        prompt = f"Explain this code in simple terms:\n{code}"

        # Generate explanation using CodeT5
        explanation = self.nlg_pipeline(
            prompt,
            max_length=150,
            num_return_sequences=1,
            temperature=0.7
        )[0]['generated_text']

        return explanation

    def get_documentation_refs(self, code: str) -> List[Dict[str, str]]:
        """Find relevant documentation references"""
        docs = []
        tree = ast.parse(code)

        # Standard library documentation
        stdlib_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    stdlib_modules.add(name.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    stdlib_modules.add(node.module.split('.')[0])

        for module in stdlib_modules:
            docs.append({
                'type': 'stdlib',
                'module': module,
                'url': f'https://docs.python.org/3/library/{module}.html'
            })

        return docs

    def analyze(self, code: str) -> CodeAnalysis:
        """Perform complete code analysis"""
        return CodeAnalysis(
            dependencies=self.extract_dependencies(code),
            potential_bugs=self.identify_bugs(code),
            explanation=self.generate_explanation(code),
            documentation_refs=self.get_documentation_refs(code)
        )


# Example usage
def test_analyzer():
    code = """
def calculate_average(numbers=[]):
    try:
        total = sum(numbers)
        return total / len(numbers)
    except:
        return 0
    """

    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze(code)

    print("Dependencies:", analysis.dependencies)
    print("\nPotential Bugs:", analysis.potential_bugs)
    print("\nExplanation:", analysis.explanation)
    print("\nDocumentation:", analysis.documentation_refs)


if __name__ == "__main__":
    test_analyzer()

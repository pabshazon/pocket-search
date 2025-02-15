from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class CodeCompletionPipeline:
    def __init__(self, model_name="microsoft/phi-3.5-mini-instruct"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model     = AutoModelForCausalLM.from_pretrained(model_name)
        # Optimize for type of backend:
        # @ todo macos because it needs specific implementation for mps.
        # if torch.backends.mps.is_available():
        #     self.device = torch.device("mps")
        # elif torch.cuda.is_available():
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        else:
            self.device = torch.device("cpu")

        self.model.to(self.device)

    def get_code_completion(self, code_context, cursor_position, max_length = 50):
        # Extract context before cursor
        code_before_cursor = code_context[:cursor_position]

        # Tokenize the input optimized for device backend.
        inputs = self.tokenizer(code_before_cursor, return_tensors="pt")
        inputs = inputs.to(self.device)

        # Generate completion
        # Turn off gradient computation
        # torch.set_grad_enabled(False)
        # Or do as below with, to turn off temporarily
        with torch.no_grad():
            outputs = self.model.generate(
                inputs["input_ids"],
                max_length=max_length,
                num_return_sequences=3,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )

        # Decode completions
        completions = []
        for output in outputs:
            decoded = self.tokenizer.decode(output, skip_special_tokens=True)
            # Extract only the newly generated part
            completion = decoded[len(code_before_cursor):].strip()
            completions.append(completion)

        return completions

def test_pipeline():
    pipeline = CodeCompletionPipeline()

    code_context = """def calculate_average(numbers):
    total = sum(numbers)
    count= len("""

    cursor_position = len(code_context)

    completions = pipeline.get_code_completion(code_context, cursor_position)

    print(completions)

test_pipeline()


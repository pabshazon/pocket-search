# This one worked but results meh
# SUMMARIZER = ModelConfig(
#         name="facebook/bart-base",
#         max_tokens_input_length=1024,
#         max_tokens_output_length=142,
#         min_tokens_output_length=56,
#         model_class=AutoModelForSeq2SeqLM,
#         device_priority=["mps", "cuda", "cpu"],
#         model_params={
#             # Model configuration parameters
#             "architectures": ["BartForConditionalGeneration"],
#             "pad_token_id": 1,
#             "bos_token_id": 0,
#             "eos_token_id": 2,
#             "decoder_start_token_id": 2,
#             "forced_eos_token_id": 2,
#
#             # Generation configuration parameters
#             "max_length": 142,
#             "min_length": 56,
#             # "length_penalty": 2.0,
#             "max_new_tokens": 1024,
#             "do_sample": False
#         }
#     )



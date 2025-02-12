import string

from transformers import AutoTokenizer, AutoModel

bert_embeddings_model_name = "bert-base-uncased"
gpt_embeddings_model_name  = "openai-gpt"

class TokenizerFactory:
    def __init__(self):
        pass

    def make(type: string):
        if type == "encoder_focus_bert":
            bert_tokenizer = AutoTokenizer.from_pretrained(bert_embeddings_model_name)
            bert_model     = AutoModel.from_pretrained(bert_embeddings_model_name)
            return         (bert_tokenizer, bert_model)
            
        elif type == "decoder_focus_gpt":
            gpt_tokenizer = AutoTokenizer.from_pretrained(gpt_embeddings_model_name)
            gpt_model     = AutoModel.from_pretrained(gpt_embeddings_model_name)
            return        (gpt_tokenizer, gpt_model)
                
        else:
            raise Exception("Unknown tokenizer type '"+type+"'.")
            
        

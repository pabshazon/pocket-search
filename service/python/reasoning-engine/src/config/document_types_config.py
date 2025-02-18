class DocumentTypesConfig:
    TYPE_PROMPT = """You are an NLP Engineer. You classify documents content into one of these categories: 
    * research
    * legal
    * finance
    *  hr
    * engineering
    * security
    * marketing
    * content_creation
    * other

    IT IS VERY IMPORTANT that you only respond with the category name, nothing else.
    It is very important that you respond a category above that exists and best describes the document.

Classify this content into one of the categories above:
{text}"""

    SUBTYPE_PROMPT = """For a {doc_type} document, classify it into one of these subtypes:
{subtypes}
Only respond with the subtype name, nothing else.

Document content:
{text}"""

    SUBTYPES_MAP = {
        "research": [
            "research_paper",
            "research_proposal",
            "research_review",
            "research_benchmark_tests",
            "other"
        ],
        "legal": [
            "nda",
            "employee_contract",
            "compliance_guideline",
            "company_bylaws",
            "company_incorporation",
            "litigation",
            "patent",
            "other"
        ],
        "finance": [
            "bank_document",
            "financial_statement",
            "financial_report",
            "financial_analysis",
            "financial_forecast",
            "other"
        ],
        "hr": [
            "cv",
            "cover_letter",
            "job_application",
            "job_interview_guidelines",
            "job_offer",
            "job_post",
            "other"
        ],
        "engineering": [
            "design_specification",
            "code",
            "documentation",
            "config",
            "infra",
            "security",
            "other"
        ],
        "security": [
            "threat_report",
            "incident_report",
            "other"
        ],
        "marketing": [
            "marketing_plan",
            "marketing_report",
            "marketing_strategy",
            "other"
        ],
        "content_creation": [
            "blog_post",
            "social_media_post",
            "email_template",
            "other"
        ],
        "other": [
            "other"
        ]
    }

    def get_type_prompt(self, document_text: str) -> str:
        """
        Generate a formatted type classification prompt for the given document text.
        
        Args:
            document_text (str): The content of the document to be classified
            
        Returns:
            str: Formatted prompt ready for classification
        """
        return self.TYPE_PROMPT.format(text=document_text)

    def get_subtype_prompt(self, document_text: str, doc_type: str) -> str:
        """
        Generate a formatted subtype classification prompt for the given document.
        
        Args:
            document_text (str): The content of the document to be classified
            doc_type (str): The main document type (must be one of the keys in SUBTYPES_MAP)
            
        Returns:
            str: Formatted prompt ready for subtype classification
            
        Raises:
            ValueError: If doc_type is not found in SUBTYPES_MAP
        """
        if doc_type not in self.SUBTYPES_MAP:
            raise ValueError(f"Unknown document type: {doc_type}")
            
        subtypes = "\n".join(self.SUBTYPES_MAP[doc_type])
        return self.SUBTYPE_PROMPT.format(
            doc_type=doc_type,
            subtypes=subtypes,
            text=document_text
        )
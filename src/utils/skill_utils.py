import re


class SkillUtils:
    """
    Utility functions for intelligent skill matching.

    Supports:
    - Exact matching
    - Synonym matching
    - Partial matching
    """

    SKILL_SYNONYMS = {

        "python": [
            "numpy",
            "pandas",
            "scikit",
            "sklearn"
        ],

        "sql": [
            "mysql",
            "postgresql",
            "postgres",
            "sqlite",
            "mssql"
        ],

        "aws": [
            "amazon web services",
            "ec2",
            "s3",
            "iam",
            "lambda",
            "cloudformation"
        ],

        "docker": [
            "container",
            "containers",
            "containerization"
        ],

        "rest api": [
            "rest",
            "fastapi",
            "flask",
            "django rest framework",
            "drf"
        ],

        "vector database": [
            "faiss",
            "pinecone",
            "milvus",
            "weaviate",
            "qdrant"
        ],

        "llm": [
            "langchain",
            "rag",
            "transformers",
            "openai",
            "anthropic",
            "gemini"
        ],

        "machine learning": [
            "ml",
            "classification",
            "regression",
            "xgboost",
            "catboost"
        ],

        "deep learning": [
            "tensorflow",
            "keras",
            "pytorch"
        ]
    }

    @staticmethod
    def contains(text: str, skill: str) -> bool:

        text = text.lower()
        skill = skill.lower()

        pattern = r"\b" + re.escape(skill) + r"\b"

        if re.search(pattern, text):
            return True

        for synonym in SkillUtils.SKILL_SYNONYMS.get(skill, []):

            pattern = r"\b" + re.escape(synonym.lower()) + r"\b"

            if re.search(pattern, text):
                return True

        return False

    @staticmethod
    def partial_contains(text: str, skill: str) -> bool:

        text = text.lower()
        skill = skill.lower()

        if skill in text:
            return True

        words = skill.split()

        if len(words) == 1:

            return False

        matched = 0

        for word in words:

            if len(word) <= 2:
                continue

            if word in text:
                matched += 1

        return matched >= max(1, len(words) // 2)

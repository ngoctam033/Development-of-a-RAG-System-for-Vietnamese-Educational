from config.prompt_templates import (
    QUESTION_NORMALIZATION_PROMPT,
    NEXT_QUERY_SUGGESTION_PROMPT,
    QA_VIET_UNI_PROMPT,
    QUESTION_CLASSIFICATION_AND_AGENTIC_STRATEGY_PROMPT,
    FINAL_ANSWER_FROM_REASONING_TRACE_PROMPT
)

PROMPT_TEMPLATES = {
    "question_normalization": {
        "template": QUESTION_NORMALIZATION_PROMPT,
        "fields": ["question"]
    },
    "next_query_suggestion": {
        "template": NEXT_QUERY_SUGGESTION_PROMPT,
        "fields": ["question", "context", "reasoning_trace"]
    },
    "qa": {
        "template": QA_VIET_UNI_PROMPT,
        "fields": ["question", "context"]
    },
    "question_classification_and_agentic_strategy": {
        "template": QUESTION_CLASSIFICATION_AND_AGENTIC_STRATEGY_PROMPT,
        "fields": ["question"]
    },
    "final_answer_from_reasoning_trace": {
        "template": FINAL_ANSWER_FROM_REASONING_TRACE_PROMPT,
        "fields": ["question", "reasoning_trace"]
    }
}

def render_prompt(template: str, fields: list, values: dict):
    missing = [f for f in fields if f not in values]
    if missing:
        raise ValueError(f"Missing fields: {missing}")
    return template.format(**values)
# Prompt maker helper
import os


PROMPT_DIR_ONLINE = "prompts/online"


def make_N1_prompt(code_list):
    with open(
        os.path.join(os.path.dirname(__file__), PROMPT_DIR_ONLINE, "N1-rule-gen.txt")
    ) as f:
        prompt_template = f.read()

    code_csv = ", ".join(sorted(code_list))
    data = {"code_list": code_csv}
    return prompt_template.format(**data)


def make_code_list_prompt(segment_name, segment_content, code_list_field_name):
    segment_data = {
        "segment_name": segment_name,
        "segment_content": segment_content,
        "code_list_field_name": code_list_field_name,
    }

    with open(
        os.path.join(os.path.dirname(__file__), PROMPT_DIR_ONLINE, "code-list-gen.txt")
    ) as f:
        prompt_template = f.read()

    return prompt_template.format(**segment_data)


def po1_extract_fields(segment_content):
    segment_data = {"segment_content": segment_content}

    with open(
        os.path.join(
            os.path.dirname(__file__), PROMPT_DIR_ONLINE, "PO1-extract-field-names.txt"
        )
    ) as f:
        prompt_template = f.read()

    return prompt_template.format(**segment_data)


def po1_extract_codes(segment_content, field_list):
    segment_data = {
        "segment_content": segment_content,
        "fields_as_csv": ", ".join(field_list),
    }

    with open(
        os.path.join(
            os.path.dirname(__file__), PROMPT_DIR_ONLINE, "PO1-code-list-extraction.txt"
        )
    ) as f:
        prompt_template = f.read()

    return prompt_template.format(**segment_data)


def po1_rule_gen(qualifier_config):

    with open(
        os.path.join(os.path.dirname(__file__), PROMPT_DIR_ONLINE, "PO1-rule-gen.txt")
    ) as f:
        prompt_template = f.read()

    return prompt_template.replace("{qualifier_config}", qualifier_config)


def make_DTM_rule_gen(qualifiers):
    with open(
        os.path.join(os.path.dirname(__file__), PROMPT_DIR_ONLINE, "DTM-rule-gen.txt")
    ) as f:
        prompt_template = f.read()

    
    data = {"qualifiers": qualifiers}
    return prompt_template.format(**data)

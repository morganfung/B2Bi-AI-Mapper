import wd
import wx
import prompt_maker as pm
import cos
import json
import re
from lxml import etree
import asyncio
from logger import logger
from presession import PresessionHandler
from mxl_indexer import MXLIndexer


INSTRUCT_USER_STR = "Rule generation failed. Please update manually."


class ComplexRule:


    def __init__(self, mxl_tree: etree._ElementTree,  element_index: MXLIndexer ,presession: PresessionHandler):
        self.presession = presession
        self.mxl_tree = mxl_tree
        self.element_index = element_index


    def add_explicit_rule_xml_structure(self, segment_name, segment_type):
        """Inject Explicit Rule xml structure into a segment or group.

        Args:
            mxl_tree (ElementTree): XML DOM
            segment_name (str): Name of the Segment or Group.
            segment_type (str): type of the segment such as Group or Segment.
        """

        explicit_rule_xml = (
            "<ExplicitRule>\n<OnBegin></OnBegin>\n<OnEnd></OnEnd>\n</ExplicitRule>"
        )
        explicit_rule = etree.fromstring(explicit_rule_xml)

        for element in self.mxl_tree.find(".//INPUT").findall(f".//{segment_type}"):
            name = element.find("./Name").text.strip()
            if name == segment_name and element.find("./ExplicitRule") is None:
                immidiate_sibling = element.find("./UsageRelatedFieldName")
                if immidiate_sibling is not None:
                    parent = immidiate_sibling.getparent()
                    index = parent.index(immidiate_sibling)
                    parent.insert(index + 1, explicit_rule)
                    return


    def inject_complex_rule(self, rule_to_inject, config):
        iterator = config.get("iterator")
        type = config.get("type")  # Group or Segment
        self.add_explicit_rule_xml_structure(config.get("name"), type)
        group = self.element_index.get_xml_element(config.get("name"), type)
        if config.get("presession"):
            self.presession.add_to_presession(config.get("presession"))
        if iterator:
            self.presession.add_to_presession(
                {
                    "declaration": f"integer {iterator};",
                    "initialization": f"{iterator}=0;",
                }
            )
            group.find(".//OnBegin").text = f"{iterator}={iterator}+1;"

        group.find(".//OnEnd").text = rule_to_inject

        logger.info(f"Rule injection done for {config.get('name')}!")


    async def complex_rule(self, document_id):
        wd_result = wd.get_enriched_document(document_id)
        doc = wd_result.get("results")[0]
        complex_rule_config = cos.get_complex_rule_config()

        tasks = []
        special_complex_rule_config = []

        for config_item in complex_rule_config:
            # REF, FOB, TD5, PO4
            if config_item.get("input_rule"):
                rule = config_item.get("input_rule").get("explicit_rule")
                self.inject_complex_rule(rule, config_item)

            # N1
            if config_item.get("name") == "4000_N1":
                tasks.append(generate_N1_rule(doc, config_item))
                special_complex_rule_config.append(config_item)
            # DTM
            if config_item.get("name") == "DTM":
                tasks.append(generate_DTM_rule(doc, config_item))
                special_complex_rule_config.append(config_item)
            # PO1
            if config_item.get("name") == "8000_PO1":
                tasks.append(generate_PO1_rule(doc, config_item))
                special_complex_rule_config.append(config_item)

        generated_rules = await asyncio.gather(*tasks)

        for generated_rule, config_item in zip(generated_rules, special_complex_rule_config):
            rule_to_inject = generated_rule
            if config_item.get("static_input_rule"):
                static_input_rule=config_item.get("static_input_rule").get("explicit_rule")
                rule_to_inject = f"{generated_rule}\n{static_input_rule}"
            self.inject_complex_rule(rule_to_inject, config_item)


# Individual complex rule functions
async def generate_N1_rule(doc, config):
    try:
        # codes/qualifier gen
        segment_name = config.get("name_in_spec", config.get("name"))
        code_list_field_name = config.get("code_list_field_name")
        segment_content = wd.get_segment_content(doc, segment_name)

        prompt = pm.make_code_list_prompt(
            segment_name, segment_content, code_list_field_name
        )
        wx_response = await wx.wx_call_async(prompt)
        extracted_code_list = json.loads(wx_response)
        logger.info("Extracted codes for N1: "+ str(extracted_code_list))

        # rule gen
        n1_code_superset = config.get("superset_codes")
        intersect = list(set(n1_code_superset) & set(extracted_code_list))
        logger.info("Interested N1 qualifiers: "+ str(intersect))
        if len(intersect)==0:
            logger.error("No interested N1 qualifier found.")
            raise Exception("No interested N1 qualifier found.")
        rule_prompt = pm.make_N1_prompt(intersect)
        result = await wx.wx_call_async(rule_prompt)
        matches = re.findall(r"```(.*?)```", result, re.DOTALL)
        if len(matches) == 0:
            logger.error("No backtick is generated by wx. Check N1 rule. "+result)
            return ""
        else:
            logger.info("Generated N1 Rule:"+ matches[0])
            return matches[0]
    except Exception as e:
        logger.error(f"Failed to generate N1 Rule. {e}")
        return INSTRUCT_USER_STR


async def generate_PO1_rule(doc, config):
    try:
        segment_name = config.get("name_in_spec", config.get("name"))
        segment_content = wd.get_segment_content(doc, segment_name)
        prompt = pm.po1_extract_fields(segment_content)
        result = await wx.wx_call_async(prompt)
        logger.info(f"Extracted fields for {segment_name}: "+ result)

        fields = json.loads(result)
        fields_with_codes = [f for f in fields if int(f[2:]) >= 106 and int(f[2:]) % 2 == 0]
        logger.info("PO1 fields with qualifier:"+ str(fields_with_codes))

        prompt = pm.po1_extract_codes(segment_content, fields_with_codes)
        result = await wx.wx_call_async(prompt)
        logger.info("Extracted qualifier for PO1: "+ result)
        extracted_qualifiers = json.loads(result)

        def calculate_offset(field_name):
            index = int(field_name[3:])
            offset = (index - 6) // 2
            return [16 + offset, 36 + offset]

        niagara_output_bucket = config.get("niagara_bucket")
        rules = []
        logger.info("Generating PO1 rules.")
        for bucket in niagara_output_bucket:

            qualifeir_config_data = []
            for qual_field in extracted_qualifiers:
                qualifiers_of_interest = list(
                    set(qual_field.get("codes")) & set(bucket.get("qualifier_superset"))
                )
                if len(qualifiers_of_interest) > 0:
                    qualifeir_config_data.append(
                        {
                            "offset": calculate_offset(qual_field.get("field_name")),
                            "qualifiers": qualifiers_of_interest,
                            "field": bucket.get("field_name"),
                        }
                    )
            if len(qualifeir_config_data) > 0:
                query = json.dumps(qualifeir_config_data, indent=2)
                prompt = pm.po1_rule_gen(query)
                result = await wx.wx_call_async(prompt)
                logger.info(result)
                rules.append(result)

        logger.info("Generated PO1 rules:"+str(rules))

        return "\n".join(rules)
    except Exception as e:
        logger.error(f"Failed to generate PO1 Rule. {e}")
        return INSTRUCT_USER_STR


async def generate_DTM_rule(doc, config):
    """Return Explicit rule for DTM Segment

    Args:
        doc (Dict): Dictionary object contain content from Watson Discovery.
        config (Dict): Segment config for DTM complex rule.
    """
    try:
        segment_name = config.get("name_in_spec", config.get("name"))
        code_list_field_name = config.get("code_list_field_name")
        segment_content = wd.get_segment_content(doc, segment_name)

        prompt = pm.make_code_list_prompt(
            segment_name, segment_content, code_list_field_name
        )
        wx_response = await wx.wx_call_async(prompt)
        try:
            logger.info("Extracted qualifier for DTM:"+ wx_response)
            qualifiers = json.loads(wx_response)
        except Exception as e:
            logger.error("Parsing failed for extracted qualifier for DTM: "+str(e))
            raise Exception(f"Failed to parse extracted qualifiers for DTM. {str(e)}")

        insterested_qualifiers = []
        if "002" in qualifiers:
            insterested_qualifiers = ["002"]
        elif "010" in qualifiers:
            insterested_qualifiers = ["010"]

        logger.info("Required qualifiers for rule gen: "+ str(insterested_qualifiers))
        rule_prompt = pm.make_DTM_rule_gen(insterested_qualifiers)
        result = await wx.wx_call_async(rule_prompt)
        return result
    except Exception as e:
        logger.error(f"Failed to generate DTM Rule. {e}")
        return INSTRUCT_USER_STR
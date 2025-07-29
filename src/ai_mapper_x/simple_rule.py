from enum import Enum
from lxml import etree
import cos
from presession import PresessionHandler
from mxl_indexer import MXLIndexer
from mxlparser import get_parents
from logger import logger


class LinkType(Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    HARDCODE = "hardcode"


class SimpleRule:
    """Class for simple rules creation and injection."""
    def __init__(self, transaction_type: str, mxl_tree: etree._ElementTree, element_index: MXLIndexer, presession: PresessionHandler):
        self.transaction_type = transaction_type
        self.mxl_tree = mxl_tree
        self.element_index = element_index
        self.presession = presession


    def get_field_element(self, field_with_parent):
        field_name = field_with_parent.get("Field").strip()
        print(field_name)
        return self.element_index.get_xml_element(field_name, "Field")


    def add_direct_link(self, field_map):

        linked_input_field = (
            field_map.get("linked_to")
            if isinstance(field_map.get("linked_to"), dict)
            else field_map.get("linked_to")[0]
        )
        input_field = self.get_field_element(linked_input_field)
        if input_field is None:
            logger.warning("Input field not found in the master xml: "+ str(linked_input_field))
            return
        input_field_id = input_field.find("./ID").text

        output_field = self.get_field_element(field_map.get("output_field"))
        link = output_field.find("./Link")
        if link is None:
            logger.info(f"Adding link for {output_field.find("Name").text}")
            link_element = etree.Element("Link")
            link_element.text = input_field_id
            store_limit = output_field.find("./StoreLimit")
            store_limit.addnext(link_element)
        else:
            logger.warning(
                f"XPath already found link for {output_field.find("Name").text}"
            )


    def inject_input_explicit_rule(self, field_map, generated_rule):

        if generated_rule.get("input_explicit_rule"):
            linked_input_field = (
                field_map.get("linked_to")
                if isinstance(field_map.get("linked_to"), dict)
                else field_map.get("linked_to")[0]
            )
            field = self.get_field_element(linked_input_field)
            if field is None:
                logger.warning("Input field not found: "+ str(linked_input_field))
            else:
                explicit_rule = field.find("./ExplicitRule")
                if explicit_rule is None:
                    explicit_element = etree.Element("ExplicitRule")
                    explicit_element.text = generated_rule.get("input_explicit_rule")
                    store_limit = field.find("./StoreLimit")
                    store_limit.addnext(explicit_element)
                else:
                    logger.info(f"Replacing explicit rule for input field: {str(linked_input_field)}")
                    explicit_rule.text = generated_rule.get("output_explicit_rule")


    def inject_output_explicit_rule(self, field_map, generated_rule):

        if generated_rule.get("output_explicit_rule"):
            # print(generated_rule)
            # print("\n\n\n")
            # print(field_map.get("output_field"))
            field = self.get_field_element(field_map.get("output_field"))
            explicit_rule = field.find("./ExplicitRule")
            if explicit_rule is None:
                explicit_element = etree.Element("ExplicitRule")
                explicit_element.text = generated_rule.get("output_explicit_rule")
                store_limit = field.find("./StoreLimit")
                store_limit.addnext(explicit_element)

            else:
                logger.info(f"Replacing explicit rule for output field: {field_map.get("output_field")}")
                explicit_rule.text = generated_rule.get("output_explicit_rule")


            # # Handle flag activation
            # active_flag = field.find("./Active")
            # if active_flag is None:
            #     active_element = etree.Element("Active")
            #     active_element.text = "1"
            #     store_limit = field.find("./StoreLimit")
            #     store_limit.addnext(active_element)
            # else:
            #     active_flag.text = "1"


    def inject_explicit_rule(self, field_map, generated_rule):
        presession = generated_rule.get("presession")
        if presession:
            self.presession.add_to_presession(generated_rule.get("presession"))

        # NOTE: injection order matters
        self.inject_input_explicit_rule(field_map, generated_rule)
        self.inject_output_explicit_rule(field_map, generated_rule)
        if field_map.get("link_type") == LinkType.DIRECT.value:
            self.add_direct_link(field_map)


    def get_simple_rule(self, rule_data):

        generated_rule = {
            "presession": rule_data.get("presession"),
            "output_explicit_rule": (
                rule_data.get("output_rule").get("explicit_rule")
                if rule_data.get("output_rule")
                else None
            ),
            "input_explicit_rule": (
                rule_data.get("input_rule").get("explicit_rule")
                if rule_data.get("input_rule")
                else None
            ),
        }

        return generated_rule


    def add_simple_rule(self):
        simple_rule_data = cos.get_simple_rule_data(self.transaction_type)
        for rule_data in simple_rule_data:
            # What is this used for? It doesn't seem like it is referenced.
            output_field = rule_data["output_field"].get("Field") if rule_data.get("output_field")  else None

            generated_rule = self.get_simple_rule(rule_data)
            self.inject_explicit_rule(rule_data, generated_rule)
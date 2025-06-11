from lxml import etree
from presession import PresessionHandler
from mxl_indexer import MXLIndexer
import cos
from logger import logger


class MonitorProHandler:
    """
    Handles the creation and injection of MonitorPro into an XML tree.
    """


    def __init__(
        self,
        element_index: MXLIndexer,
        presession: PresessionHandler,
    ):
        self.presession = presession
        self.element_index = element_index


    def inject(self):
        """
        Injects monitorpro rule into the XML node.
        """
        logger.info("Processing MonitorPro.")
        for rule in cos.get_monitorpro_data():
            if rule.get("name") == "presession":
                self.presession.add_to_presession(rule.get("rule"))
            else:
                field = self.element_index.get_xml_element(rule.get("name"), "Field")
                explicit_rule = field.find("./ExplicitRule")
                if explicit_rule is None:
                    explicit_element = etree.Element("ExplicitRule")
                    explicit_element.text = rule.get("explicit_rule")
                    store_limit = field.find("./StoreLimit")
                    store_limit.addnext(explicit_element)
                else:
                    logger.warning(f"Explicit rule already exist for {rule.get("name")}. Appending.")
                    explicit_rule.text = (
                        f'{explicit_rule.text}\n{rule.get("explicit_rule")}'
                    )

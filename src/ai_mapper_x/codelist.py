from mxl_indexer import MXLIndexer
from logger import logger


CODELIST_RULE_TEMPLATE="""
if $4000_N1[i].#0098:6="SF" THEN
BEGIN
SELECT receivercode INTO $850.#TEMP_N1_SF FROM CODELIST WHERE Name = "{0}" and sendercode = $4000_N1[i].#0067:3;
END
"""

class CodelistHandler:
    """
    Handles external codelist an XML tree.
    """


    def __init__(
        self,
        element_index: MXLIndexer,
    ):
        self.element_index = element_index


    def inject(self, codelist_name: str):
        """
        Inject external codelist rule into XML node.
        """
        logger.info("Processing External codelist.")
        n1_group = self.element_index.get_xml_element("4000_N1", "Group")
        # ***CHECK***: set try except pass to continue testing
        try:
            n1_group.find(".//OnEnd").text += "\n" + CODELIST_RULE_TEMPLATE.format(codelist_name)
        except:
            pass
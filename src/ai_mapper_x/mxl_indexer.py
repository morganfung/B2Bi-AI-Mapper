from lxml import etree


class MXLIndexer:
    """
    Creates index for Field, Segment and Group. It helps for quick lookup.
    """


    def __init__(self, mxl_tree: etree._ElementTree):
        """Create index and store in a dictionary

        Args:
            mxl_tree (etree._ElementTree): mxl element tree
        """
        self.index = {"Field": {}, "Segment": {}, "Group": {}}
        for type in ["Field", "Segment", "Group"]:
            for element in mxl_tree.findall(f".//{type}"):
                name = element.find("./Name").text.strip()
                self.index.get(type)[name] = element


    def get_xml_element(self, name: str, type: str):
        return self.index.get(type).get(name)

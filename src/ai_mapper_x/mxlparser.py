from lxml import etree


NS = "http://www.stercomm.com/SI/Map"


def remove_namespace(tree, namespace):
    ns = "{%s}" % namespace
    nsl = len(ns)
    for elem in tree.iter():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]


def load_xml(file_path):
    tree = etree.parse(file_path)
    remove_namespace(tree, NS)
    return tree


def get_parents(element):
    parents = {}
    while element is not None:
        name_element = element.find("./Name")
        if name_element is not None:
            parents[element.tag] = element.find("./Name").text
        element = element.getparent()
    return parents
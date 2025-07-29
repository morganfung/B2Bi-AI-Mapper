from dotenv import load_dotenv

load_dotenv()

from lxml import etree
import uuid
from mxlparser import load_xml
import cos
import asyncio

from logger import logger
from mxl_indexer import MXLIndexer
from presession import PresessionHandler
from simple_rule import SimpleRule
from complex_rule import ComplexRule
from monitorpro import MonitorProHandler
from codelist import CodelistHandler


TRANSACTION_TYPE = "810"


async def generate_map_file(
    transaction_type: str, document_id: str, partner_account_number: str = "", codelist_name: str = ""
) -> str:
    """Generate map file.

    Args:
        transaction_type (str): The transction type number as a string
        document_id (str): The ID of the Watson Discover document.
                           This is used to identify the document for which
                           the MXL file is being generated.
        partner_account_number (str, optional): The Niagara account number for the partner. Defaults to "".
        codelist_name (str, optional): The name of the codelist. Defaults to "".

    Returns:
        str: The UUID of the generated MXL file.
    """
    mxl_tree = load_xml(cos.get_master_mxl(transaction_type))

    element_index = MXLIndexer(mxl_tree)
    presession = PresessionHandler()

    # print(mxl_tree)

    # create partner account variable in presession
    presession.add_to_presession(
        {
            "declaration": f"STRING[200] PARTNER_ACCOUNT;",
            "initialization": f'PARTNER_ACCOUNT="{partner_account_number}";',
        }
    )
    simple_rule = SimpleRule(transaction_type, mxl_tree, element_index, presession)
    complex_rule = ComplexRule(transaction_type, mxl_tree, element_index, presession)
    monitorpro = MonitorProHandler(transaction_type, element_index, presession)

    simple_rule.add_simple_rule()
    monitorpro.inject()
    await complex_rule.complex_rule(document_id)
    if codelist_name != "":
        CodelistHandler(element_index).inject(codelist_name)

    # should inject presession after generating all rules
    presession.inject(mxl_tree)
    mxl_string = etree.tostring(
        mxl_tree, encoding="UTF-8", pretty_print=True, xml_declaration=True
    )
    mxl_id = uuid.uuid4()
    cos.create_object(f"{TRANSACTION_TYPE}/generated_mxl/{mxl_id}.mxl", mxl_string)

    return mxl_id


async def main():
    ## User Input
    # NEED TO MAKE CHANGES TO WD COLLECTION ROUTING
    DOCUMENT_ID = "4e960f80-08c5-465a-9af9-55bc0134c38a" # 99 cent
    ACCOUNT_NUMBER = "123"
    CODELIST_NAME = "DUMMY_SHIP_FROM"
    mxl_id = await generate_map_file(TRANSACTION_TYPE, DOCUMENT_ID, ACCOUNT_NUMBER, CODELIST_NAME)
    logger.info(f"MXL FILE ID: {mxl_id}")


if __name__ == "__main__":
    asyncio.run(main())
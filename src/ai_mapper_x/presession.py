from logger import logger

class PresessionHandler:
    """
    Handles the creation and injection of pre-session rule into an XML tree.
    """


    def __init__(self):
        """
        Initializes the PresessionHandler with empty strings for declaration and initialization.
        """
        self.presession_declaration = ""
        self.precession_initialization = ""


    def add_to_presession(self, presession):
        """
        Adds a pre-session entry to the declaration and initialization strings.

        Args:
            presession (dict): A dictionary containing 'declaration' and 'initialization' keys.
        """
        declarations = presession.get("declaration")
        initializations = presession.get("initialization")

        if isinstance(declarations, list) and not isinstance(initializations, list):
            logger.error("1: Issue with presession variables.")
            raise Exception("1: Issue with presession variables.")
        
        elif isinstance(initializations, list) and not isinstance(declarations, list):
            logger.error("2: Issue with presession variables.")
            raise Exception("2: Issue with presession variables.")
        
        elif isinstance(declarations, list) and isinstance(initializations, list):
            if len(declarations) != len(initializations):
                logger.error("3: Issue with presession variables.")
                raise Exception("3: Issue with presession variables.")
            for dec in declarations:
                self.presession_declaration += dec + "\n"
            for init in initializations:
                self.precession_initialization += init + "\n"
            
        else:
            self.presession_declaration += declarations + "\n"
            self.precession_initialization += initializations + "\n"


    def inject(self, mxl_tree):
        """
        Injects the accumulated pre-session data into the specified XML node.

        Args:
            mxl_tree (object): The XML tree object to modify.  Assumes it has a PreSessionRule element'.
        """
        mxl_tree.find(".//PreSessionRule").text = (
            f"{self.presession_declaration}\n{self.precession_initialization}"
        )
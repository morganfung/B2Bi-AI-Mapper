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
        self.presession_declaration += presession.get("declaration") + "\n"
        self.precession_initialization += presession.get("initialization") + "\n"


    def inject(self, mxl_tree):
        """
        Injects the accumulated pre-session data into the specified XML node.

        Args:
            mxl_tree (object): The XML tree object to modify.  Assumes it has a PreSessionRule element'.
        """
        mxl_tree.find(".//PreSessionRule").text = (
            f"{self.presession_declaration}\n{self.precession_initialization}"
        )
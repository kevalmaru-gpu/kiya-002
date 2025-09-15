from core.tool.tool_class import Tool


class FormatInitialLeadsTool(Tool):
    """
    Tool for formatting initial lead data with company information.
    Extracts and validates company name, description, and location data.
    """
    
    def __init__(self):
        # Define the input schema for lead data
        input_schema = {
            "company_name": {
                "type": "string",
                "required": True,
                "description": "The name of the company"
            },
            "company_description": {
                "type": "string", 
                "required": True,
                "description": "A brief description of what the company does"
            },
            "location": {
                "type": "string",
                "required": True,
                "description": "The physical location or address of the company"
            },
            "website": {
                "type": "string",
                "required": True,
                "description": "The website of the company"
            },
            "linkedin_url": {
                "type": "string",
                "required": True,
                "description": "The LinkedIn URL of the company"
            }
        }
        
        super().__init__(
            name="format_initial_leads",
            description="Formats and validates initial lead data containing company information",
            input_schema=input_schema
        )
    
    def run(self, input_data):
        """
        Executes the tool with the provided lead data.
        Simply returns the input data as-is for formatting purposes.
        
        Args:
            input_data: List of dictionaries containing company information
                       Each dictionary should have company_name, company_description, and location
            
        Returns:
            List[Dict]: The same input data passed to the function
        """
        return {
            "success": True,
            "response": input_data
        }

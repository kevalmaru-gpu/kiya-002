from typing import Union
from typing import Any
import pandas as pd
import os
from datetime import datetime
from core.tool.tool_class import Tool

class ExportLeadsToDocTool(Tool):
    def __init__(self):
        super().__init__(name="ExportLeadsToDocTool", description="Export leads to an Excel file.")

    def get_input_schema_prompt(self) -> str:
        return """
        ExportLeadsToDocTool Input Schema:
        The input should be a dictionary with the following required fields:
        [
            {
                "company_name": "string (required) - The name of the company",
                "website": "string (required) - The company's website URL",
                "location": "string (required) - The company's location/address",
                "phone_number": "array of strings (required) - List of phone numbers for the company",
                "email": "array of strings (required) - List of email addresses for the company"
            }
        ]
        
        Example:
        [
            {
                "company_name": "Acme Corporation",
                "website": "https://www.acme.com",
                "location": "123 Business St, City, State 12345",
                "phone_number": ["+1-555-123-4567", "+1-555-987-6543"],
                "email": ["contact@acme.com", "sales@acme.com", "info@acme.com"]
            }
        ]
        """
    
    def validate_input_schema(self, input_data: Any) -> Union[bool, str]:
        """
        Validate that input_data matches the expected schema for ExportLeadsToDocTool.
        
        Expected schema:
        - input_data should be a list of dictionaries
        - Each dictionary should have: company_name, website, location, phone_number, email
        - company_name, website, location should be strings
        - phone_number and email should be lists of strings
        
        Returns:
        - True if validation passes
        - Error message string if validation fails
        """
        try:
            # Check if input_data is a list
            if not isinstance(input_data, list):
                return "Input data must be a list of lead dictionaries"
            
            # Check if list is not empty
            if not input_data:
                return "Input data cannot be an empty list"
            
            # Validate each lead dictionary in the list
            for i, lead in enumerate(input_data):
                if not isinstance(lead, dict):
                    return f"Lead at index {i} must be a dictionary"
                
                # Check required fields
                required_fields = ["company_name", "website", "location", "phone_number", "email"]
                for field in required_fields:
                    if field not in lead:
                        return f"Lead at index {i} is missing required field: {field}"
                
                # Validate company_name
                if not isinstance(lead["company_name"], str) or not lead["company_name"].strip():
                    return f"Lead at index {i}: company_name must be a non-empty string"
                
                # # Validate website
                # if not isinstance(lead["website"], str) or not lead["website"].strip():
                #     return f"Lead at index {i}: website must be a non-empty string"
                
                # # Validate location
                # if not isinstance(lead["location"], str) or not lead["location"].strip():
                #     return f"Lead at index {i}: location must be a non-empty string"
                
                # # Validate phone_number
                # if not isinstance(lead["phone_number"], list):
                #     return f"Lead at index {i}: phone_number must be a list"
                
                # if not lead["phone_number"]:  # Check if list is not empty
                #     return f"Lead at index {i}: phone_number list cannot be empty"
                
                # for j, phone in enumerate(lead["phone_number"]):
                #     if not isinstance(phone, str) or not phone.strip():
                #         return f"Lead at index {i}, phone_number at index {j}: must be a non-empty string"
                
                # Validate email
                # if not isinstance(lead["email"], list):
                #     return f"Lead at index {i}: email must be a list"
                
                # if not lead["email"]:  # Check if list is not empty
                #     return f"Lead at index {i}: email list cannot be empty"
                
                # for j, email in enumerate(lead["email"]):
                #     if not isinstance(email, str) or not email.strip():
                #         return f"Lead at index {i}, email at index {j}: must be a non-empty string"
                    
                #     # Basic email format validation
                #     if "@" not in email or "." not in email.split("@")[-1]:
                #         return f"Lead at index {i}, email at index {j}: invalid email format"
            
            return True
            
        except Exception as e:
            return f"Validation error: {str(e)}"

    def run(self, input_data: Any) -> Any:
        """
        Export leads data to an Excel file and save it to the local system.
        
        Args:
            input_data: List of lead dictionaries containing company information
            
        Returns:
            Dictionary with success status and file path information
        """
        try:
            # Validate input data first
            validation_result = self.validate_input_schema(input_data)
            if validation_result != True:
                return {
                    "success": False,
                    "server_error": False,
                    "error": f"Input validation failed: {validation_result}"
                }
            
            # Create a directory for exports if it doesn't exist
            export_dir = "exports"
            if not os.path.exists(export_dir):
                os.makedirs(export_dir)
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"leads_export_{timestamp}.xlsx"
            filepath = os.path.join(export_dir, filename)
            
            # Prepare data for Excel export
            excel_data = []
            for lead in input_data:
                # Join phone numbers and emails with semicolons for better readability
                phone_numbers = "; ".join(lead["phone_number"])
                email_addresses = "; ".join(lead["email"])
                
                excel_data.append({
                    "Company Name": lead["company_name"],
                    "Website": lead["website"],
                    "Location": lead["location"],
                    "Phone Numbers": phone_numbers,
                    "Email Addresses": email_addresses
                })
            
            # Create DataFrame and export to Excel
            df = pd.DataFrame(excel_data)
            
            # Export to Excel with formatting
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='Leads', index=False)
                
                # Get the workbook and worksheet for formatting
                workbook = writer.book
                worksheet = writer.sheets['Leads']
                
                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)  # Cap at 50 characters
                    worksheet.column_dimensions[column_letter].width = adjusted_width
                
                # Add header formatting
                from openpyxl.styles import Font, PatternFill, Alignment
                header_font = Font(bold=True, color="FFFFFF")
                header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
                header_alignment = Alignment(horizontal="center", vertical="center")
                
                for cell in worksheet[1]:
                    cell.font = header_font
                    cell.fill = header_fill
                    cell.alignment = header_alignment
            
            # Get absolute file path
            absolute_filepath = os.path.abspath(filepath)
            
            return {
                "success": True,
                "message": f"Successfully exported {len(input_data)} leads to Excel file",
                "filepath": absolute_filepath,
                "filename": filename,
                "total_leads": len(input_data)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to export leads to Excel: {str(e)}"
            }